from ..clients.data import (
    ApiClient,
    Configuration,
    DataSetServiceApi,
    DataTableServiceApi,
)
from .common import BaseElevateClient, BaseElevateService


class DataClient(BaseElevateClient, ApiClient):
    _route = "/api/data"
    _conf_class = Configuration


class DataTableService(BaseElevateService, DataTableServiceApi):
    _client_class = DataClient


class DataSetService(BaseElevateService, DataSetServiceApi):
    _client_class = DataClient
