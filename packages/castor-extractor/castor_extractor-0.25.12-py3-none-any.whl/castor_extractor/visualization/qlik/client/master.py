from typing import Callable, Optional

from tqdm import tqdm  # type: ignore

from ..assets import QlikAsset
from .constants import APP_EXTERNAL_ID_KEY, SCOPED_ASSETS
from .engine import EngineApiClient, QlikCredentials
from .rest import RestApiClient

ListedData = list[dict]


class MissingAppsScopeError(Exception):
    """
    Error to be raised when the scope on apps was required and not provided
    """

    def __init__(self, asset: QlikAsset):
        error_msg = f"App ids must be provided to fetch {asset}."
        super().__init__(error_msg)


def _include_app_external_id(
    data: ListedData,
    app_external_id: str,
) -> ListedData:
    _data = data.copy()
    for element in _data:
        element.update({"app_external_id": app_external_id})
    return _data


def _fetch_children_on_apps(
    apps: ListedData,
    fetch_callback: Callable,
    display_progress: bool,
) -> ListedData:
    all_apps_data: ListedData = list()
    apps_iterator = apps if not display_progress else tqdm(apps)
    for app in apps_iterator:
        app_id = app[APP_EXTERNAL_ID_KEY]
        data = fetch_callback(app_id)
        data = _include_app_external_id(data, app_id)
        all_apps_data.extend(data)
    return all_apps_data


class QlikMasterClient:
    """
    Qlik master client acts as a wrapper class on top of Qlik RestApiClient and
    EngineApiClient to fetch assets regardless of the underlying API.
    """

    def __init__(
        self,
        credentials: QlikCredentials,
        except_http_error_statuses: Optional[list[int]] = None,
        display_progress: bool = True,
    ):
        self._server_url = credentials.base_url
        self.display_progress = display_progress

        self.rest_api_client = RestApiClient(
            credentials=credentials,
            except_http_error_statuses=except_http_error_statuses,
        )

        self.engine_api_client = EngineApiClient(credentials=credentials)

    def _fetch_lineage(self, apps: ListedData) -> ListedData:
        callback = self.rest_api_client.data_lineage
        return _fetch_children_on_apps(apps, callback, self.display_progress)

    def _fetch_measures(self, apps: ListedData) -> ListedData:
        callback = self.engine_api_client.measures
        return _fetch_children_on_apps(apps, callback, self.display_progress)

    def fetch(
        self,
        asset: QlikAsset,
        *,
        apps: Optional[ListedData] = None,
    ) -> ListedData:
        """
        Given a QlikAsset, returns the corresponding data using the
        appropriate client.

        Note:
            QlikAsset.LINEAGE and QlikAsset.MEASURES must be provided a
            scope on app_ids
        """
        if asset in SCOPED_ASSETS and not apps:
            raise MissingAppsScopeError(asset)

        if asset == QlikAsset.MEASURES:
            assert apps  # can't be False as we priorly checked
            return self._fetch_measures(apps)

        if asset == QlikAsset.LINEAGE:
            assert apps  # can't be False as we priorly checked
            return self._fetch_lineage(apps)

        return self.rest_api_client.get(asset)
