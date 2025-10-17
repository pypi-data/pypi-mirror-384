import logging
from typing import Optional

import tableauserverclient as TSC  # type: ignore

from ....utils import SerializedAsset
from ..assets import TABLEAU_PULSE_ASSETS, TableauAsset
from ..constants import CREDENTIALS_SITE_ID_KEY, DEFAULT_TIMEOUT_SECONDS
from .client_metadata_api import TableauClientMetadataApi
from .client_rest_api import TableauClientRestApi
from .client_tsc import TableauClientTSC
from .credentials import TableauCredentials

logger = logging.getLogger(__name__)

# these assets must be extracted via TableauServerClient (TSC)
_TSC_ASSETS = (
    # projects are not available in Metadata API
    TableauAsset.PROJECT,
    # view count are not available in Metadata API
    TableauAsset.USAGE,
    # only users who published content can be extracted from MetadataAPI
    TableauAsset.USER,
)

# these assets must be extracted via the REST API
_REST_API_ASSETS = (
    # Tableau Pulse assets are only available in REST API
    TableauAsset.METRIC,
    TableauAsset.METRIC_DEFINITION,
    TableauAsset.SUBSCRIPTION,
)

logging.getLogger("tableau.endpoint").setLevel(logging.WARNING)


def _add_site_id(workbooks: SerializedAsset, site_id: str) -> SerializedAsset:
    """
    Add site_id from credentials: it's necessary to compute workbook's url
    """
    for workbook in workbooks:
        workbook[CREDENTIALS_SITE_ID_KEY] = site_id
    return workbooks


def _merge_datasources(
    datasources: SerializedAsset,
    tsc_datasources: SerializedAsset,
) -> SerializedAsset:
    """
    Enrich datasources with fields coming from TableauServerClient:
    - project_luid
    - webpage_url
    """

    mapping = {row["id"]: row for row in tsc_datasources}

    for datasource in datasources:
        if datasource["__typename"] != "PublishedDatasource":
            # embedded datasources are bound to workbooks => no project
            # embedded datasources cannot be accessed via URL => no webpage_url
            continue
        luid = datasource["luid"]
        tsc_datasource = mapping.get(luid)
        if not tsc_datasource:
            # it happens that a datasource is in Metadata API but not in TSC
            datasource["projectLuid"] = None
            datasource["webpageUrl"] = None
            continue
        datasource["projectLuid"] = tsc_datasource["project_id"]
        datasource["webpageUrl"] = tsc_datasource["webpage_url"]

    return datasources


def _merge_workbooks(
    workbooks: SerializedAsset,
    tsc_workbooks: SerializedAsset,
) -> SerializedAsset:
    """
    Enrich workbooks with fields coming from TableauServerClient:
    - project_luid
    """

    mapping = {row["id"]: row for row in tsc_workbooks}

    for workbook in workbooks:
        luid = workbook["luid"]
        tsc_workbook = mapping.get(luid)
        if not tsc_workbook:
            # it happens that a workbook is in Metadata API but not in TSC
            # in this case, we push the workbook with default project
            logger.warning(f"Workbook {luid} was not found in TSC")
            workbook["projectLuid"] = None
            continue

        workbook["projectLuid"] = tsc_workbook["project_id"]

    return workbooks


def _server(
    server_url: str,
    timeout_sec: int,
    ignore_ssl: bool = False,
) -> TSC.Server:
    verify = not ignore_ssl
    options = {"verify": verify, "timeout": timeout_sec}
    server = TSC.Server(server_url, use_server_version=True)
    server.add_http_options(options)
    return server


class TableauClient:
    """
    Connect to Tableau's API and extract assets.

    Relies on TableauServerClient (TSC) overlay for authentication
    https://tableau.github.io/server-client-python/docs/
    """

    def __init__(
        self,
        credentials: TableauCredentials,
        timeout_sec: int = DEFAULT_TIMEOUT_SECONDS,
        with_columns: bool = True,
        with_fields: bool = True,
        with_pulse: bool = False,
        override_page_size: Optional[int] = None,
        ignore_errors: bool = False,
        ignore_ssl: bool = False,
    ):
        self._credentials = credentials
        self._server = _server(
            server_url=credentials.server_url,
            timeout_sec=timeout_sec,
            ignore_ssl=ignore_ssl,
        )
        self._with_columns = with_columns
        self._with_fields = with_fields
        self._with_pulse = with_pulse
        self._ignore_errors = ignore_errors

        self._client_metadata = TableauClientMetadataApi(
            server=self._server,
            override_page_size=override_page_size,
        )
        self._client_rest = TableauClientRestApi(server=self._server)
        self._client_tsc = TableauClientTSC(server=self._server)

    @property
    def base_url(self) -> str:
        return self._credentials.server_url

    @property
    def name(self) -> str:
        return "Tableau/API"

    def _user_password_login(self) -> None:
        """Login into Tableau using user and password"""
        self._server.auth.sign_in(
            TSC.TableauAuth(
                self._credentials.user,
                self._credentials.password,
                site_id=self._credentials.site_id,
            ),
        )

    def _pat_login(self) -> None:
        """Login into Tableau using personal authentication token"""
        self._server.auth.sign_in(
            TSC.PersonalAccessTokenAuth(
                self._credentials.token_name,
                self._credentials.token,
                site_id=self._credentials.site_id,
            ),
        )

    def login(self) -> None:
        """
        Depending on the given credentials, logs-in using either:
        - user/password
        - token_name/value (Personal Access Token)
        https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_auth.htm

        Raises an error if none can be found
        """

        if self._credentials.user and self._credentials.password:
            logger.info("Logging in using user and password authentication")
            return self._user_password_login()

        if self._credentials.token_name and self._credentials.token:
            logger.info("Logging in using token authentication")
            return self._pat_login()

        raise ValueError(
            "Invalid credentials: either user/password or PAT must be provided",
        )

    def _fetch_datasources(self) -> SerializedAsset:
        asset = TableauAsset.DATASOURCE

        datasources = self._client_metadata.fetch(asset)
        tsc_datasources = self._client_tsc.fetch(asset)

        return _merge_datasources(datasources, tsc_datasources)

    def _fetch_workbooks(self) -> SerializedAsset:
        asset = TableauAsset.WORKBOOK

        site_id = self._credentials.site_id
        workbooks = self._client_metadata.fetch(asset)
        workbooks = _add_site_id(workbooks, site_id)

        workbook_projects = self._client_tsc.fetch(asset)

        return _merge_workbooks(workbooks, workbook_projects)

    def fetch(
        self,
        asset: TableauAsset,
    ) -> SerializedAsset:
        """
        Extract the given Tableau Asset
        """
        if asset in TABLEAU_PULSE_ASSETS and not self._with_pulse:
            logger.info(f"Skipping asset {asset} - Tableau Pulse de-activated")
            return []

        if asset == TableauAsset.COLUMN and not self._with_columns:
            logger.info(f"Skipping asset {asset} - deactivated columns")
            return []

        if asset == TableauAsset.FIELD and not self._with_fields:
            logger.info(f"Skipping asset {asset} - deactivated fields")
            return []

        logger.info(f"Extracting {asset.name}...")

        if asset == TableauAsset.DATASOURCE:
            # two APIs are required to extract datasources
            return self._fetch_datasources()

        if asset == TableauAsset.WORKBOOK:
            # two APIs are required to extract workbooks
            return self._fetch_workbooks()

        if asset in _TSC_ASSETS:
            # some assets can only be extracted via TSC
            return self._client_tsc.fetch(asset)

        if asset in _REST_API_ASSETS:
            # some assets can only be extracted via REST API
            return self._client_rest.fetch(asset)

        # other assets can be extracted via Metadata API
        return self._client_metadata.fetch(asset, self._ignore_errors)
