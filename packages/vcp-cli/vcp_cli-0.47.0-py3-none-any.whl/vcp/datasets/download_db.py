import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel

from .api import SearchResponse, search_data_api


class DownloadCandidate(BaseModel):
    dataset_id: str
    dataset_name: str
    namespace: Optional[str]
    location: str
    downloaded: bool = False


class DownloadDatabase:
    """Manages SQLite database for download candidates with expiration support."""

    def __init__(self, downloads_dir: Optional[str] = None):
        if downloads_dir is None:
            downloads_dir = os.path.expanduser("~/.vcp/downloads")
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def _get_db_path(self, search_term: str, expiration_date: datetime) -> Path:
        """Generate database filename with expiration date."""
        safe_term = "".join(c for c in search_term if c.isalnum() or c in ("-", "_"))[
            :50
        ]
        expiry_str = expiration_date.strftime("%Y%m%d")
        return self.downloads_dir / f"candidates_{safe_term}_{expiry_str}.db"

    def create_candidates_db(
        self, search_term: str, query: str
    ) -> Tuple[Path, sqlite3.Connection]:
        """Create SQLite database for download candidates."""
        expiration_date = datetime.now() + timedelta(days=1)
        db_path = self._get_db_path(search_term, expiration_date)

        conn = sqlite3.connect(str(db_path))

        # Create query metadata table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_metadata (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                search_term TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # Create download candidates table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS download_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                namespace TEXT,
                location TEXT NOT NULL,
                downloaded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dataset_id ON download_candidates(dataset_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_downloaded ON download_candidates(downloaded)
        """)

        # Insert query metadata
        conn.execute(
            """
            INSERT INTO query_metadata (query, search_term, expires_at)
            VALUES (?, ?, ?)
        """,
            (query, search_term, expiration_date),
        )

        conn.commit()
        return db_path, conn

    def insert_candidates(
        self, conn: sqlite3.Connection, candidates: List[DownloadCandidate]
    ) -> None:
        """Insert download candidates into the database."""
        conn.executemany(
            """
            INSERT INTO download_candidates 
            (dataset_id, dataset_name, namespace, location, downloaded)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    c.dataset_id,
                    c.dataset_name,
                    c.namespace,
                    c.location,
                    int(c.downloaded),
                )
                for c in candidates
            ],
        )
        conn.commit()

    def get_pending_candidates(self, db_path: Path) -> List[DownloadCandidate]:
        """Get all non-downloaded candidates from the database."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("""
            SELECT dataset_id, dataset_name, namespace, location, downloaded
            FROM download_candidates
            WHERE downloaded = 0
            ORDER BY id
        """)

        candidates = []
        for row in cursor.fetchall():
            candidates.append(
                DownloadCandidate(
                    dataset_id=row[0],
                    dataset_name=row[1],
                    namespace=row[2],
                    location=row[3],
                    downloaded=bool(row[4]),
                )
            )
        conn.close()
        return candidates

    def mark_downloaded(self, db_path: Path, dataset_id: str, location: str) -> None:
        """Mark a specific candidate as downloaded."""
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """
            UPDATE download_candidates 
            SET downloaded = 1 
            WHERE dataset_id = ? AND location = ?
            """,
            (dataset_id, location),
        )
        conn.commit()
        conn.close()

    def find_existing_candidates_db(self, query: str) -> Optional[Path]:
        """Find existing non-expired candidates database for the given query."""
        now = datetime.now()

        for db_file in self.downloads_dir.glob("candidates_*.db"):
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.execute("""
                    SELECT query, expires_at FROM query_metadata LIMIT 1
                """)
                row = cursor.fetchone()
                conn.close()

                if row:
                    stored_query, expires_at_str = row
                    expires_at = datetime.fromisoformat(expires_at_str)

                    # Check if query matches and not expired
                    if stored_query == query and expires_at > now:
                        return db_file

            except Exception:
                # Skip corrupted databases
                continue

        return None

    def get_database_stats(self, db_path: Path) -> Tuple[int, int]:
        """Get total and pending candidate counts from database."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN downloaded = 0 THEN 1 END) as pending
            FROM download_candidates
        """)
        row = cursor.fetchone()
        conn.close()
        return row[0], row[1]  # total, pending

    def cleanup_expired_databases(self) -> int:
        """Remove expired candidate databases. Returns count of removed databases."""
        now = datetime.now()
        removed_count = 0

        for db_file in self.downloads_dir.glob("candidates_*.db"):
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.execute("""
                    SELECT expires_at FROM query_metadata LIMIT 1
                """)
                row = cursor.fetchone()
                conn.close()

                if row:
                    expires_at = datetime.fromisoformat(row[0])
                    if expires_at <= now:
                        db_file.unlink()
                        removed_count += 1

            except Exception:
                # Remove corrupted databases too
                db_file.unlink()
                removed_count += 1

        return removed_count

    def collect_candidates_from_search(
        self, query: str, id_token: str, limit: int = 100, exact: bool = False
    ) -> Path:
        """Collect all candidates by exhausting search cursors."""
        db_path, conn = self.create_candidates_db(query, query)

        try:
            # Start transaction - don't commit until we're done
            conn.execute("BEGIN TRANSACTION")

            cursor = None
            total_collected = 0
            completed_successfully = False

            while True:
                resp = search_data_api(id_token, query, limit, cursor, exact=exact)

                candidates = []
                for item in resp.data:
                    namespace = getattr(item, "namespace", None)
                    for location in item.locations:
                        if hasattr(location, "path"):
                            location_str = location.path
                        elif hasattr(location, "url"):
                            location_str = location.url
                        else:
                            location_str = str(location)
                        candidates.append(
                            DownloadCandidate(
                                dataset_id=item.internal_id,
                                dataset_name=item.name,
                                namespace=namespace,
                                location=location_str,
                            )
                        )

                if candidates:
                    # Insert without commit
                    conn.executemany(
                        """
                        INSERT INTO download_candidates 
                        (dataset_id, dataset_name, namespace, location, downloaded)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                c.dataset_id,
                                c.dataset_name,
                                c.namespace,
                                c.location,
                                int(c.downloaded),
                            )
                            for c in candidates
                        ],
                    )
                    total_collected += len(candidates)

                cursor = resp.cursor
                last_page = resp.limit is not None and len(resp.data) < resp.limit
                if last_page or not cursor:
                    completed_successfully = True
                    break

            if completed_successfully:
                # Only commit if we completed the full search
                conn.commit()
                print(f"✅ Collected {total_collected} download candidates")
                return db_path
            else:
                # This shouldn't happen, but safety check
                conn.rollback()
                db_path.unlink(missing_ok=True)  # Remove incomplete database
                raise Exception("Search collection was not completed successfully")

        except Exception as e:
            # Rollback and cleanup on any error or interruption
            conn.rollback()
            db_path.unlink(missing_ok=True)  # Remove incomplete database
            print(f"❌ Candidate collection failed or was interrupted: {e}")
            raise

        finally:
            conn.close()


def extract_candidates_from_response(resp: SearchResponse) -> List[DownloadCandidate]:
    """Extract download candidates from a search response."""
    candidates = []
    for item in resp.data:
        namespace = getattr(item, "namespace", None)
        for location in item.locations:
            if hasattr(location, "path"):
                location_str = location.path
            elif hasattr(location, "url"):
                location_str = location.url
            else:
                location_str = str(location)
            candidates.append(
                DownloadCandidate(
                    dataset_id=item.internal_id,
                    dataset_name=item.name,
                    namespace=namespace,
                    location=location_str,
                )
            )
    return candidates
