import logging
from collections.abc import Iterable, Iterator
from typing import Union

from ...utils import (
    OUTPUT_DIR,
    current_timestamp,
    deep_serialize,
    from_env,
    get_output_filename,
    write_json,
    write_summary,
)
from .assets import ThoughtspotAsset
from .client import (
    ThoughtspotClient,
    ThoughtspotCredentials,
)

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: ThoughtspotClient,
) -> Iterable[tuple[ThoughtspotAsset, Union[list, Iterator, dict]]]:
    """Iterate over the extracted data from Thoughtspot"""

    for asset in ThoughtspotAsset:
        logger.info(f"Extracting {asset.value} from API")
        data = client.fetch(asset)
        yield asset, deep_serialize(data)


def extract_all(**kwargs) -> None:
    """
    Extract data from Thoughtspot API
    Store the output files locally under the given output_directory
    """
    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)

    credentials = ThoughtspotCredentials(**kwargs)
    client = ThoughtspotClient(credentials=credentials)

    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), _output_directory, ts)
        write_json(filename, list(data))

    write_summary(_output_directory, ts, host=credentials.base_url)
