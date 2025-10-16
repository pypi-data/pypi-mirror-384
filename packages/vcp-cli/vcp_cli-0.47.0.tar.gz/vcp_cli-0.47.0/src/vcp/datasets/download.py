import contextlib
import os
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterator, List, Optional, cast
from urllib.parse import urlparse

import boto3
import requests
from boto3.s3.transfer import S3Transfer, TransferConfig
from botocore import UNSIGNED
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_s3.client import S3Client
from pydantic import BaseModel
from rich.console import Console

from .api import DatasetSizeModel, Location, LocationModel, get_credentials_for_datasets
from .download_db import DownloadDatabase

console = Console()

MAX_WORKERS = 10  # TODO:[EM] this should be configurable


class S3Credentials(BaseModel):
    """
    These ephemeral credentials will be provided by authenticated requests to the data-api
    """

    access_key_id: str
    secret_access_key: str
    session_token: str

    def dump_args(self) -> dict:
        return {
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_access_key,
            "aws_session_token": self.session_token,
        }


# stream content from http request into file, with option to show progress bar
def http_stream_one(uri: str, outdir: str, show_progress: bool = True) -> None:
    asset_name = urlparse(uri).path.split("/")[-1]
    outfile = os.path.join(outdir, asset_name)
    console.print(f"⬇️  {asset_name}")
    try:
        with requests.get(uri, stream=True) as r:
            # raise an exception if an http response indicates error
            r.raise_for_status()

            # calculate total expected bytes
            total_bytes = int(r.headers.get("content-length", 0))
            with open(outfile, "wb") as fw:
                with progress_bar_ctx(total_bytes, show_progress) as pbar:
                    # fetch 8182 bytes - efficient block size chunk
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            fw.write(chunk)
                        if show_progress:
                            pbar.update(len(chunk))
            console.print("[green]✅ HTTP stream succeeded! [/green]")
    except Exception as e:
        # clean up
        if os.path.exists(outfile):
            os.remove(outfile)
        console.print(f"[red]❌ HTTP stream failed: {e}[/red]")


def list_s3_objects(uri: str, s3: S3Client) -> List[str]:
    """
    List all objects in an S3 bucket with a given prefix.
    Returns a list of full S3 URIs for each object found.
    """
    parsed = urlparse(uri)
    bucket_name, prefix = parsed.netloc, parsed.path.lstrip("/")

    # Ensure prefix ends with / if it's meant to be a folder
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    objects = []
    paginator = s3.get_paginator("list_objects_v2")

    try:
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    # Skip directory markers (objects ending with /)
                    if not obj["Key"].endswith("/"):
                        s3_uri = f"s3://{bucket_name}/{obj['Key']}"
                        objects.append(s3_uri)

        if not objects:
            console.print(
                f"[yellow]⚠️  No objects found with prefix {prefix} in bucket {bucket_name}[/yellow]"
            )

        return objects

    except (BotoCoreError, ClientError) as e:
        console.print(f"[red]❌ Failed to list S3 objects: {e}[/red]")
        return []


def is_s3_prefix(uri: str, s3: S3Client) -> bool:
    """
    Check if a URI points to a single file or a prefix (folder).
    Returns True if it's a prefix, False if it's a single file.
    """
    parsed = urlparse(uri)
    bucket_name, key = parsed.netloc, parsed.path.lstrip("/")

    try:
        # Try to get object metadata - if it succeeds, it's a single file
        s3.head_object(Bucket=bucket_name, Key=key)
        return False
    except ClientError as e:
        if e.response["Error"]["Code"] in {"404", "403"}:
            # Object doesn't exist, might be a prefix. Including 403 as it will be returned if the user does not have
            # list access to the bucket at root level.
            return True
        else:
            # Other error, re-raise
            raise


# stream content from s3 into file or folder, with option show progress bar
def s3_stream_one(
    uri: str, outdir: str, s3: S3Client, show_progress: bool = True
) -> None:
    # Check if this is a prefix (folder) or single file
    is_prefix = is_s3_prefix(uri, s3)
    if is_prefix:
        # Handle folder download
        s3_objects = list_s3_objects(uri, s3)
        if not s3_objects:
            return

        dir_name = uri.split("/")[-1]
        console.print(
            f"⬇️  Downloading {len(s3_objects)} objects from folder: {dir_name}"
        )

        # TODO: parallelize this download
        # Download each object in the folder
        for obj_uri in s3_objects:
            path = obj_uri.replace(uri, "").split("/")[:-1]
            # Create the directory structure if it doesn't exist
            if path:
                outdir_with_prefix = os.path.join(outdir, dir_name, *path)
                os.makedirs(outdir_with_prefix, exist_ok=True)

            _s3_stream_single_file(obj_uri, outdir_with_prefix, s3, show_progress)

        console.print(
            f"[green]✅ S3 folder download completed! Downloaded {len(s3_objects)} files[/green]"
        )
    else:
        # Handle single file download
        console.print(f"⬇️  {uri.split('/')[-1]}")
        _s3_stream_single_file(uri, outdir, s3, show_progress)
        console.print("[green]✅ S3 stream succeeded! [/green]")


def _s3_stream_single_file(
    uri: str, outdir: str, s3: S3Client, show_progress: bool = True
) -> None:
    """Internal function to download a single S3 file."""
    parsed = urlparse(uri)
    bucket_name, asset_path = parsed.netloc, parsed.path.lstrip("/")
    asset_name = asset_path.split("/")[-1]
    outfile = os.path.join(outdir, asset_name)
    try:
        # prefetch size
        total_size = s3.head_object(Bucket=bucket_name, Key=asset_path)["ContentLength"]

        # configure s3 transfer
        cfg = TransferConfig(
            multipart_threshold=16 * 1024 * 1024,
            multipart_chunksize=16 * 1024 * 1024,
            max_concurrency=8,
        )

        with progress_bar_ctx(total_size, show_progress) as pbar:
            S3Transfer(s3, cfg).download_file(
                bucket_name,
                asset_path,
                outfile,
                callback=lambda bytes_amount: (
                    pbar.update(bytes_amount) if show_progress else None
                ),
            )

    except (BotoCoreError, ClientError) as e:
        # clean up
        if os.path.exists(outfile):
            os.remove(outfile)
        console.print(f"[red]❌ S3 stream failed: {e}[/red]")


# s3 batch streaming
def s3_stream_batch(
    s3_uri: List[str], outdir: str, creds: S3Credentials, show_progress=True
):
    """
    batch download of s3 files
    """
    # Try authenticated access first
    s3 = cast(S3Client, boto3.client("s3", **creds.dump_args()))

    # Test if credentials work by trying to access the first URI
    if s3_uri:
        test_uri = s3_uri[0]
        parsed = urlparse(test_uri)
        bucket_name = parsed.netloc
        prefix = parsed.path.lstrip("/")

        try:
            s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in {"403", "AccessDenied"}:
                # Create anonymous S3 client for public buckets
                s3 = cast(
                    S3Client,
                    boto3.client("s3", config=BotoConfig(signature_version=UNSIGNED)),
                )
            else:
                raise

    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        ex.map(
            lambda u: s3_stream_one(u, outdir, s3, show_progress=show_progress), s3_uri
        )


# batch stream content http/s schema locations
def http_stream_batch(uris: List[str], outdir: str, show_progress: bool = True) -> None:
    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        ex.map(lambda u: http_stream_one(u, outdir, show_progress=show_progress), uris)


# progress factory  -----------------------------------------------------------
@contextlib.contextmanager
def progress_bar_ctx(total: int, progress: bool = True) -> Iterator[Any]:
    """
    Context manager to create a progress bar.
    """
    if progress:
        try:
            from tqdm import tqdm  # noqa: PLC0415
        except ModuleNotFoundError as e:
            raise ImportError(
                "tqdm is not installed. Please install it to use progress bars."
            ) from e

        pbar = tqdm(total=total, unit="B", unit_scale=True)
        try:
            yield pbar
        finally:
            pbar.close()
    else:
        yield contextlib.nullcontext()


# ───────────────────────────────────────────────────────────────────────────────
# Generic downloader  (http/https + s3 w/ temp creds)
# ───────────────────────────────────────────────────────────────────────────────
def download_locations(
    locations: List[Location],
    creds: Optional[S3Credentials],
    outdir: str = ".",
):
    """
    Download every http(s) or s3 link in *locations*.

    • creds may hold STS keys: {access_key_id, secret_access_key, session_token}
    • Uses tqdm if installed.
    """
    # split links ---------------------------------------------------------------
    http_links, s3_links = [], []
    for loc in locations:
        if isinstance(loc, str):
            parsed_url = urlparse(loc)
        elif isinstance(loc, LocationModel):
            parsed_url = urlparse(loc.path)
        elif isinstance(loc, DatasetSizeModel):
            parsed_url = urlparse(loc.url)
        else:
            raise Exception("Unrecognized location type:")
        full_url, scheme = (
            f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}",
            parsed_url.scheme,
        )

        if scheme in ("http", "https", "cellxgene"):
            http_links.append(full_url)
        elif scheme in ("s3"):
            s3_links.append(full_url)
        else:
            console.print(f"Unknown scheme {scheme}: {full_url}")

    if not http_links and not s3_links:
        console.print("No downloadable links found.")
        return

    os.makedirs(outdir, exist_ok=True)

    # HTTP/S downloads ----------------------------------------------------------
    http_stream_batch(http_links, outdir=outdir, show_progress=True)

    # S3 downloads --------------------------------------------------------------
    if creds is None and len(s3_links):
        console.print("[red]❌ Must pass credentials to download from s3[/red]")
        return
    elif len(s3_links):
        assert isinstance(creds, S3Credentials)
        s3_stream_batch(s3_links, outdir, creds)


def download_from_candidates_db(
    db_path: str,
    id_token: str,
    outdir: str = ".",
    max_parallel_datasets: int = 5,
) -> None:
    """
    Download files from SQLite candidates database with parallel downloads and individual credential fetching.
    """
    db = DownloadDatabase()
    candidates = db.get_pending_candidates(Path(db_path))

    if not candidates:
        console.print("✅ All candidates already downloaded or no candidates found.")
        return

    console.print(f"📦 Found {len(candidates)} pending downloads")
    os.makedirs(outdir, exist_ok=True)

    # Group candidates by dataset ID
    candidates_by_dataset = {}
    for candidate in candidates:
        if candidate.dataset_id not in candidates_by_dataset:
            candidates_by_dataset[candidate.dataset_id] = []
        candidates_by_dataset[candidate.dataset_id].append(candidate)

    dataset_ids = list(candidates_by_dataset.keys())
    total_datasets = len(dataset_ids)

    def download_single_dataset(dataset_id: str) -> tuple:
        """Download a single dataset by getting its credentials and downloading all files."""
        dataset_candidates = candidates_by_dataset[dataset_id]
        dataset_name = dataset_candidates[0].dataset_name

        try:
            # Convert candidates to locations first to check if we need S3 credentials
            locations_to_download = []
            has_s3_locations = False

            for candidate in dataset_candidates:
                # TODO (ebezzi): handle the gs:// case here as well
                if candidate.location.startswith(("http://", "https://")):
                    locations_to_download.append(candidate.location)
                else:
                    # Assume s3 for everything else (s3:// URLs or bare paths)
                    locations_to_download.append(
                        LocationModel(scheme="s3", path=candidate.location)
                    )
                    has_s3_locations = True

            # Only get credentials if we have S3 locations
            dataset_creds = None
            if has_s3_locations:
                creds_response = get_credentials_for_datasets(id_token, [dataset_id])
                actual_creds = creds_response.get("credentials")
                if not actual_creds:
                    console.print(
                        f"[red]❌ No S3 credentials returned for dataset {dataset_id}[/red]"
                    )
                    console.print(
                        "[yellow]   Please ensure you have the necessary permissions to access this dataset[/yellow]"
                    )
                    return (
                        dataset_id,
                        dataset_candidates,
                        dataset_name,
                        False,
                        "No S3 credentials available",
                    )

                dataset_creds = S3Credentials.model_validate(actual_creds)

            # Download all locations for this dataset
            download_locations(locations_to_download, dataset_creds, outdir)

            return (dataset_id, dataset_candidates, dataset_name, True, None)

        except Exception as e:
            return (dataset_id, dataset_candidates, dataset_name, False, str(e))

    console.print(
        f"🚀 Starting parallel download of {total_datasets} datasets (max {max_parallel_datasets} concurrent)..."
    )

    # Download all datasets in parallel with immediate shutdown on CTRL-C
    executor = ThreadPoolExecutor(max_workers=max_parallel_datasets)

    try:
        # Submit all download tasks
        future_to_dataset = {
            executor.submit(download_single_dataset, dataset_id): dataset_id
            for dataset_id in dataset_ids
        }

        # Process completed downloads
        completed = 0
        for future in as_completed(future_to_dataset):
            _, dataset_candidates, dataset_name, success, error = future.result()
            completed += 1

            if success:
                # Mark all candidates as downloaded
                for candidate in dataset_candidates:
                    db.mark_downloaded(
                        Path(db_path), candidate.dataset_id, candidate.location
                    )
                console.print(
                    f"[green]✅ [{completed}/{total_datasets}] Downloaded {dataset_name}[/green]"
                )
            else:
                console.print(
                    f"[red]❌ [{completed}/{total_datasets}] Failed to download {dataset_name}: {error}[/red]"
                )

        console.print("🎉 Download from candidates database completed!")

    except KeyboardInterrupt:
        console.print(
            "\n[yellow]⚠️  Download interrupted by user. Shutting down...[/yellow]"
        )
        # Cancel all pending futures
        for future in future_to_dataset:
            future.cancel()
        console.print(
            "🔄 Run the same command again to resume from where you left off."
        )

    finally:
        # Force immediate shutdown without waiting
        executor.shutdown(wait=False)
