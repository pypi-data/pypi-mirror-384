from metorial_util_endpoint import (
  BaseMetorialEndpoint,
  MetorialEndpointManager,
  MetorialRequest,
)
from ..resources import (
  mapDashboardInstanceServersGetOutput,
  DashboardInstanceServersGetOutput,
)


class MetorialServersEndpoint(BaseMetorialEndpoint):
  """A server represents a deployable MCP server in Metorial's catalog. You can use server deployments to create MCP server instances that you can connect to."""

  def __init__(self, config: MetorialEndpointManager):
    super().__init__(config)

  def get(self, server_id: str) -> DashboardInstanceServersGetOutput:
    """
    Get server by ID
    Retrieves detailed information for a server identified by its ID.

    :param server_id: str
    :return: DashboardInstanceServersGetOutput
    """
    request = MetorialRequest(path=["servers", server_id])
    return self._get(request).transform(mapDashboardInstanceServersGetOutput.from_dict)
