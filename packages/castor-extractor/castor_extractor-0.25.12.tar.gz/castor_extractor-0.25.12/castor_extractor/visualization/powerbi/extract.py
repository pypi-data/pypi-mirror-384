import json
import logging
from collections.abc import Iterable
from typing import Optional, Union

from ...utils import (
    OUTPUT_DIR,
    current_timestamp,
    deep_serialize,
    from_env,
    get_output_filename,
    write_json,
    write_summary,
)
from .assets import PowerBiAsset
from .client import PowerbiCertificate, PowerbiClient, PowerbiCredentials

logger = logging.getLogger(__name__)


def _load_certificate(
    certificate: Optional[str],
) -> Optional[PowerbiCertificate]:
    if not certificate:
        return None

    with open(certificate) as file:
        cert = json.load(file)
        return PowerbiCertificate(**cert)


def iterate_all_data(
    client: PowerbiClient,
) -> Iterable[tuple[PowerBiAsset, Union[list, dict]]]:
    for asset in PowerBiAsset:
        if asset in PowerBiAsset.optional:
            continue

        logger.info(f"Extracting {asset.name} from API")
        data = list(deep_serialize(client.fetch(asset)))
        yield asset, data
        logger.info(f"Extracted {len(data)} {asset.name} from API")


def extract_all(**kwargs) -> None:
    """
    Extract data from PowerBI REST API
    Store the output files locally under the given output_directory
    """
    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    creds = PowerbiCredentials(
        client_id=kwargs.get("client_id"),
        tenant_id=kwargs.get("tenant_id"),
        secret=kwargs.get("secret"),
        certificate=_load_certificate(kwargs.get("certificate")),
        api_base=kwargs.get("api_base"),
        login_url=kwargs.get("login_url"),
        scopes=kwargs.get("scopes"),
    )
    client = PowerbiClient(creds)
    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), _output_directory, ts)
        write_json(filename, data)

    write_summary(_output_directory, ts)
