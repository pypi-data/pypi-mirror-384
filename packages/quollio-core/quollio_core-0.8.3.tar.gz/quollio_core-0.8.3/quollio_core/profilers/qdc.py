import logging
from io import BytesIO
from typing import Dict

import fastavro

from quollio_core.helper.core import new_global_id
from quollio_core.models.avroasset import AvroAsset
from quollio_core.repository import qdc

logger = logging.getLogger(__name__)


def gen_existing_global_id_dict(avro_content: bytes) -> Dict[str, bool]:
    byte_io = BytesIO(avro_content)
    avro_schema = AvroAsset.avro_schema_to_python()
    reader = fastavro.reader(byte_io, avro_schema)
    records = {record["id"]: True for record in reader}
    return records


def get_avro_file_content(tenant_id: str, account_id: str, qdc_client: qdc.QDCExternalAPIClient) -> bytes:
    datasource_id = new_global_id(tenant_id=tenant_id, cluster_id=account_id, data_id="", data_type="data_source")
    logger.debug("Datasource id: {dsrc_id}".format(dsrc_id=datasource_id))
    res = qdc_client.get_export_url(datasource_id=datasource_id)
    file_content = qdc_client.download_file(res).content
    return file_content
