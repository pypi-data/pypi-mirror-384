from typing import Optional, Callable

import grpc

from .evaluation_details import DataSource
from .grpc.generated.statsig_forward_proxy_pb2 import ConfigSpecRequest  # pylint: disable=no-name-in-module
from .grpc.generated.statsig_forward_proxy_pb2_grpc import StatsigForwardProxyStub
from .interface_network import IStatsigNetworkWorker, NetworkProtocol
from .statsig_context import InitContext
from .statsig_options import ProxyConfig


class GRPCWorker(IStatsigNetworkWorker):
    def __init__(self, sdk_key: str, proxy_config: ProxyConfig, context: InitContext):
        self.sdk_key = sdk_key
        self.proxy_config = proxy_config
        channel = grpc.insecure_channel(proxy_config.proxy_address)
        self.channel = channel
        self.stub = StatsigForwardProxyStub(channel)
        self.context = context

    @property
    def type(self) -> NetworkProtocol:
        return NetworkProtocol.GRPC

    def is_pull_worker(self) -> bool:
        return False

    def get_dcs(self, on_complete: Callable, since_time: int = 0, log_on_exception: Optional[bool] = False,
                init_timeout: Optional[int] = None):
        request = ConfigSpecRequest(sdkKey=self.sdk_key, sinceTime=since_time)
        try:
            self.context.source_api = self.proxy_config.proxy_address
            response = self.stub.getConfigSpec(request)
            on_complete(DataSource.NETWORK, response.spec, None)
        except Exception as e:
            on_complete(DataSource.NETWORK, None, e)

    def get_id_lists(self, on_complete: Callable, log_on_exception: Optional[bool] = False,
                     init_timeout: Optional[int] = None):
        raise NotImplementedError('Not supported yet')

    def log_events(self, payload, headers=None, log_on_exception=False, retry=0):
        raise NotImplementedError('Not supported yet')

    def shutdown(self) -> None:
        self.channel.close()
