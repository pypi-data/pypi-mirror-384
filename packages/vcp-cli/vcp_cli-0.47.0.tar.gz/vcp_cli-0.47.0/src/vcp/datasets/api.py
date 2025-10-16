import typing
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, ConfigDict, HttpUrl, computed_field, model_validator
from pydantic.fields import Field

from vcp.config.config import Config


@lru_cache(maxsize=1)
def _get_config():
    """lazily load the config (this allows overriding in tests)"""
    return Config.load()


def _build_data_api_url(path: str) -> str:
    """
    Build a complete data API URL by joining base_url with the given path.
    Ensures proper URL construction regardless of trailing slash in base_url.

    Args:
        path: Relative path to append to base URL (e.g., "data/credentials")

    Returns:
        Complete URL with base_url and path properly joined
    """
    base_url = _get_config().data_api.base_url
    if not base_url.endswith("/"):
        base_url += "/"
    return urljoin(base_url, path)


class LocationModel(BaseModel):
    scheme: str  # one of "s3","http","https","cellxgene"
    path: str


class DatasetSizeModel(BaseModel):
    url: str
    contentSize: Optional[int] = None


Location = Union[LocationModel, str, DatasetSizeModel]


class DataItemSimplified(BaseModel):
    internal_id: str
    name: str = Field(..., description="Curator provided name for the dataset")
    locations: List[Location] = Field(default=[])
    tags: List[str] = Field(default=[])
    license: Optional[Union[HttpUrl, str]] = Field(default="")
    doi: Optional[Union[HttpUrl, str]] = Field(default="")
    domain: Optional[str] = Field(default="unknown")

    @model_validator(mode="before")
    @classmethod
    def handle_name_label(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If 'name' is not present but 'label' is, use 'label' as 'name'
            if "name" not in data and "label" in data:
                data["name"] = data["label"]
            # If both are present, 'name' takes precedence (do nothing)
        return data

    @computed_field(alias="namespace")
    @property
    def namespace(self) -> Optional[str]:
        namespace = [
            tag.split(":")[1] for tag in self.tags if tag.startswith("namespace:")
        ]
        if namespace:
            return namespace[0]

    model_config = ConfigDict(extra="allow", validate_by_alias=True)


class CrossModalitySchemaFields(BaseModel):
    """
    Biological metadata fields from Cross-Modality Schema (XMS)

    NOTE: These fields use aliases for display names in CLI output.
    NOTE: The field order is used for CLI output
    """

    # Using alias for display names in CLI output
    assay: List[str] = Field(
        default=[],
        alias="Assay",
        description="Defines the assay that was used to create the dataset. Human Readable label",
    )
    assay_ontology_term_id: List[str] = Field(
        default=[],
        alias="Assay Ontology Term ID",
        description="Defines the assay that was used to create the dataset. MUST be an Experimental Factor Ontology (EFO) term such as “EFO:0022605”",
    )
    tissue: List[str] = Field(
        default=[],
        alias="Tissue",
        description="Defines the tissues from which assayed biosamples were derived. Human Readable label",
    )
    tissue_ontology_term_id: List[str] = Field(
        default=[],
        alias="Tissue Ontology Term ID",
        description="Defines the tissues from which assayed biosamples were derived. Allowed ontologies are Cell Ontology (CL), Gene Ontology (GO), Uberon (UBERON), C. elegans Gross Anatomy (WBbt), Zebrafish Anatomy Ontology (ZFA), Drosophila Anatomy Ontology (FBbt).",
    )
    organism: List[str] = Field(
        default=[],
        alias="Organism",
        description="Defines the organism from which assayed biosamples were derived. Human Readable label",
    )
    organism_ontology_term_id: List[str] = Field(
        default=[],
        alias="Organism Ontology Term ID",
        description="Defines the organism from which assayed biosamples were derived. MUST be an NCBI organismal classification term such as 'NCBITaxon:9606'",
    )
    disease: List[str] = Field(
        default=[],
        alias="Disease",
        description="Defines the disease of the patients or organisms from which assayed biosamples were derived. Human Readable label",
    )
    disease_ontology_term_id: List[str] = Field(
        default=[],
        alias="Disease Ontology Term ID",
        description="Defines the disease of the patients or organisms from which assayed biosamples were derived. MUST be most accurate descendant of 'MONDO:0000001' if disease, or 'PATO:0000461' for normal or healthy.",
    )
    tissue_type: Optional[List[str]] = Field(
        default=None,
        alias="Tissue Type",
        description="One of 'cell culture', 'cell line', 'organelle', 'organoid', 'tissue'.",
    )
    cell_type: Optional[List[str]] = Field(default=None, alias="Cell Type")
    development_stage: List[str] = Field(
        default=[],
        alias="Development Stage",
        description="Defines the development stage(s) of the patients or organisms from which assayed biosamples were derived. Human Readable label",
    )
    development_stage_ontology_term_id: List[str] = Field(
        default=[],
        alias="Development Stage Ontology Term ID",
        description="Defines the development stage(s) of the patients or organisms from which assayed biosamples were derived. 'na' if drawn from a cell line, 'unknown' if unkown' or otherwise an ontology term from an organism specific ontology.",
    )

    model_config = ConfigDict(populate_by_name=True)


class DataItem(DataItemSimplified, CrossModalitySchemaFields):
    """Data item with both basic fields and biological metadata"""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class DatasetResponse(BaseModel):
    credentials: Dict[str, Any]
    locations: List[Location] = Field(default=[])


class SearchResponse(BaseModel):
    credentials: Dict[str, Any] = Field(default_factory=dict)
    data: List[DataItem | DataItemSimplified] = Field(default_factory=list)
    limit: Optional[int] = None
    total: Optional[int] = None
    page_limit: Optional[int] = None
    cursor: Optional[str] = None
    offset: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def handle_null_credentials(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("credentials") is None:
            data["credentials"] = {}
        return data

    model_config = ConfigDict(extra="allow")


class PreviewResponse(BaseModel):
    dataset_id: str
    neuroglancer_url: str
    zarr_files: List[str]
    dataset_label: str


class FacetBucket(BaseModel):
    value: str
    count: int


class SummaryResponse(BaseModel):
    field: str
    query: str
    total_buckets: int
    facets: List[FacetBucket]


# wrapper to hitting the data-api with credentials
def _call_data_api(id_token: str, endpoint: str, params: dict) -> Union[dict, str]:
    hdrs = {"Authorization": f"Bearer {id_token}", "Accept": "application/json"}
    r = requests.get(endpoint, params=params, headers=hdrs, timeout=30)
    r.raise_for_status()
    return (
        r.json()
        if r.headers.get("content-type", "").startswith("application/json")
        else r.text
    )


def _process_search_term(query_term: str, exact: bool) -> str:
    """
    Processes a search term to ensure it is formatted correctly for querying.

    Args:
       query_term (str): The search term to process.
       exact (bool): A flag indicating whether the search should be an exact match.

    Returns:
       str: The processed search term. If `exact` is True and the term is not already
       wrapped in quotes, it will be wrapped in double quotes to enforce an exact match.
       Otherwise, the term is returned as-is.

    Notes:
       - If the `exact` flag is False, the term is returned without modification.
       - If the term is already wrapped in double quotes, it is returned as-is.
       - This function does not currently handle filters or boolean operators in the query.
    """
    if not exact or (query_term.startswith('"') and query_term.endswith('"')):
        return query_term
    # exact match - wrap in quotes
    return f'"{query_term}"'


def search_data_api(
    id_token: str,
    term: str,
    limit: int,
    cursor: Optional[str] = None,
    exact: bool = False,
) -> SearchResponse:
    processed_term = _process_search_term(term, exact)

    params = {
        "query": processed_term,
        "use_cursor": "true",
        "download": "true",  # always true to get creds
        "scout": not bool(cursor),  # only scout on first page
    }
    if cursor:
        params["cursor"] = cursor

    data = _call_data_api(
        id_token, f"{_get_config().data_api.base_url}/search", params=params
    )

    if isinstance(data, str):
        raise Exception(f"Invalid search response: {data}")

    # create object without validation - from a trusted source
    return SearchResponse.model_validate(data)


# entrypoint to call the data-api "summary" resource with credentials.
def summary_data_api(
    id_token: str,
    field: str,
    term: str = "*",
    size: int = 1000,
    cursor: Optional[str] = None,
) -> SummaryResponse:
    params = {
        "field": field,
        "query": term,
        "size": size,
    }

    data = _call_data_api(
        id_token, f"{_get_config().data_api.base_url}/summarize", params=params
    )

    if isinstance(data, str):
        raise Exception(f"Invalid search response: {data}")

    # create object without validation - from a trusted source
    return SummaryResponse.model_validate(data)


class Identifier(BaseModel):
    name: str
    value: str


class StructuredValue(BaseModel):
    name: str
    identifier: Identifier


class PropertyValue(BaseModel):
    """Schema.org PropertyValue for variableMeasured"""

    type: Optional[str] = Field(None, alias="@type")
    name: str
    value: Optional[
        Union[
            None,
            str,
            int,
            float,
            bool,
            Dict[str, Any],
            StructuredValue,
            List[StructuredValue],
            List[str],
            List[bool],
            List[int],
            List[float],
        ]
    ] = None
    # value: Union[
    #     None, str, int, float, bool, StructuredValue
    # ]
    description: Optional[str] = None
    propertyID: Optional[str] = None
    additionalProperty: Optional[List["PropertyValue"]] = None


class CroissantFileObject(BaseModel):
    """Croissant FileObject for distribution items"""

    type: str = Field(alias="@type", default="cr:FileObject")
    id: str = Field(alias="@id")
    name: str
    description: Optional[str] = None
    content_url: HttpUrl = Field(alias="contentUrl")
    content_size: Optional[str] = Field(None, alias="contentSize")
    encoding_format: str = Field(alias="encodingFormat")
    sha256: Optional[str] = None


class Creator(BaseModel):
    """Creator object in Croissant metadata"""

    type: str = Field(alias="@type")  # e.g., "Organization" or "Person"
    name: str
    url: Optional[HttpUrl] = None


class CroissantLiteModel(BaseModel):
    """Croissant Lite metadata model for the md field"""

    context: Optional[Dict[str, Any]] = Field(None, alias="@context")
    type: Optional[str] = Field("sc:Dataset", alias="@type")
    conforms_to: Optional[HttpUrl] = Field(None, alias="conformsTo")

    # Basic metadata
    name: Optional[str] = None
    url: Optional[str] = Field(None, description="Webpage URL of the dataset")
    description: Optional[str] = ""
    version: Optional[str] = None
    license: Optional[HttpUrl | str] = None

    # Attribution
    creator: Optional[Union[Creator, List[Creator], Dict[str, Any]]] = None
    citation: Optional[Union[HttpUrl, str]] = None
    cite_as: Optional[str] = Field(None, alias="citeAs")

    # Content metadata
    keywords: List[str] | str = Field(default_factory=list)
    variable_measured: List[PropertyValue] = Field(
        default_factory=list, alias="variableMeasured"
    )
    distribution: List[Union[CroissantFileObject, Dict[str, Any]]] = Field(
        default_factory=list
    )

    # Additional fields
    about: Optional[Dict[str, Any]] = None  # DefinedTerm for domain
    date_published: Optional[str] = Field(None, alias="datePublished")

    # Sometimes keywords is a string, so we need to convert it to a list
    @model_validator(mode="before")
    @classmethod
    def handle_keywords_string(cls, data: Any) -> Any:
        if isinstance(data, dict) and "keywords" in data:
            keywords_value = data["keywords"]
            if isinstance(keywords_value, str):
                data["keywords"] = [keywords_value]
        return data

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def model_post_init(self, __context):
        """
        Ensures that keywords is always a list after model initialization.
        """
        if isinstance(self.keywords, str):
            self.keywords = [self.keywords]


# Keep FileObject for backward compatibility but it maps to the root-level format
class FileObject(BaseModel):
    """Represents items in distribution (backward compatibility)"""

    id: str = Field(..., alias="@id")
    name: str
    description: Optional[str]
    content_url: HttpUrl = Field(..., alias="contentUrl")
    encoding_format: str = Field(..., alias="encodingFormat")
    sha256: Optional[str]


class DatasetRecord(BaseModel):
    """
    Dataset record from the API response.
    The md field contains Croissant Lite metadata.
    """

    # Core fields from the API response
    internal_id: str
    label: str
    type: str
    external_id: str

    # Optional metadata fields
    domain: Optional[str] = None
    owner: Optional[str] = ""
    org: Optional[str] = None
    version: Optional[str] = None  # This might come from root or md

    # Collections and relationships
    locations: List[Location] = Field(default_factory=list)
    scopes: Optional[List[str]] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    version_of: List[str] = Field(default_factory=list)
    transformation_of: List[str] = Field(default_factory=list)

    # Credentials (when download=true)
    credentials: Optional[Dict[str, str]] = Field(default=None)

    # Croissant Lite metadata
    md: Optional[CroissantLiteModel] = None

    # Legacy fields for backward compatibility (these should come from md)
    distribution: Optional[List[FileObject]] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def handle_null_scopes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Convert None scopes to empty list
            if data.get("scopes") is None:
                data["scopes"] = []
        return data

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, arbitrary_types_allowed=True
    )

    def namespace(self) -> Optional[str]:
        """Extract namespace from tags"""
        namespace = [
            tag.split(":")[1] for tag in self.tags if tag.startswith("namespace:")
        ]
        if namespace:
            return namespace[0]
        return None


# Factory Functions for Creating DataItem from DatasetRecord
def extract_biological_metadata(
    croissant_model: Optional[CroissantLiteModel],
) -> Dict[str, Any]:
    """
    Extract biological metadata from CroissantLiteModel's variableMeasured.

    Returns a dict of field_name -> value suitable for CrossModalitySchemaFields.
    """
    bio_fields = {}

    if not croissant_model or not croissant_model.variable_measured:
        return bio_fields

    # Get field names from CrossModalitySchemaFields
    xms_fields = CrossModalitySchemaFields.model_fields

    for field_name in xms_fields.keys():
        for pv in croissant_model.variable_measured:
            if pv.name == field_name:
                value = pv.value
                if value is not None:
                    # Check if field expects a list
                    field_info = xms_fields[field_name]
                    annotation = field_info.annotation

                    # Handle Optional[List[str]] type annotations
                    if typing.get_origin(annotation) is Union:
                        # Get the non-None type from Optional
                        args = typing.get_args(annotation)
                        annotation = next(
                            (arg for arg in args if arg is not type(None)), annotation
                        )

                    if typing.get_origin(annotation) is list:
                        bio_fields[field_name] = (
                            value if isinstance(value, list) else [value]
                        )
                    else:
                        bio_fields[field_name] = value
                break

    return bio_fields


def create_data_item_from_dataset(record: DatasetRecord) -> DataItem:
    """
    Factory function to create a DataItem from a DatasetRecord.

    This extracts biological metadata from the Croissant metadata and
    combines it with basic fields from the dataset record.
    """
    # Extract biological metadata from the md field
    bio_fields = extract_biological_metadata(record.md)

    # Create DataItem with both basic and biological fields
    return DataItem(
        internal_id=record.internal_id,
        name=record.label,
        locations=record.locations,
        tags=record.tags,
        **bio_fields,
    )


def create_cross_modality_fields_from_dataset(
    record: DatasetRecord,
) -> CrossModalitySchemaFields:
    """
    Factory function to create CrossModalitySchemaFields from a DatasetRecord.

    This extracts only the biological metadata from the Croissant metadata
    and returns a CrossModalitySchemaFields object.
    """
    # Extract biological metadata from the md field
    bio_fields = extract_biological_metadata(record.md)

    # Create and return CrossModalitySchemaFields with the extracted fields
    # Note: We use populate_by_name=True in the model_config, so field names work
    return CrossModalitySchemaFields.model_validate(bio_fields)


# entrypoint to call the data-api "dataset" resource with credentials
def get_dataset_api(id_token: str, dataset_id: str, download: bool) -> DatasetRecord:
    data = get_dataset_api_raw(id_token, dataset_id, download)
    return DatasetRecord.model_validate(data)


def get_dataset_api_raw(
    id_token: str, dataset_id: str, download: bool
) -> DatasetRecord:
    data = _call_data_api(
        id_token,
        f"{_get_config().data_api.base_url}/dataset/{dataset_id}",
        {"download": str(download).lower()},
    )

    if isinstance(data, str):
        raise Exception(f"Invalid search response: {data}")

    return data


def get_credentials_for_datasets(
    id_token: str, dataset_ids: List[str]
) -> Dict[str, Any]:
    """
    Get temporary AWS credentials for a batch of dataset IDs via POST /credentials endpoint.
    NOTE (ebezzi): due to limitations with the size of the AWS policy (2048 characters), this command should,
    for now, only be invoked with a single dataset. Otherwise it might fail upstream and return empty credentials.
    This might get fixed in the future
    """
    if not dataset_ids:
        raise ValueError("At least one dataset ID is required")

    # Use same authentication pattern as existing API calls
    hdrs = {
        "Authorization": f"Bearer {id_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {"ids": dataset_ids}
    url = _build_data_api_url("credentials")

    r = requests.post(url, headers=hdrs, json=payload, timeout=30)
    r.raise_for_status()

    return r.json()


def preview_data_api(id_token: str, dataset_id: str) -> PreviewResponse:
    data = _call_data_api(
        id_token,
        f"{_get_config().data_api.base_url}/preview/{dataset_id}",
        {},
    )
    return PreviewResponse.model_validate(data)
