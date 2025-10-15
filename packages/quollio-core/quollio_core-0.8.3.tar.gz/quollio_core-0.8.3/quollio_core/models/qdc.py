from dataclasses import asdict, dataclass
from typing import Dict


@dataclass
class GetImportURLRequest:
    service_name: str
    source_name: str
    file_name: str
    override_logical_name: str
    update_mode: str

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class DataSourceMetadataResponseBody:
    user_id: str
    job_key: str
    service_name: str
    source_name: str
    source_type: str
    override_logical_name: str

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class GetImportURLResponse:
    location: str
    datasource_metadata_response_body: DataSourceMetadataResponseBody

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)
