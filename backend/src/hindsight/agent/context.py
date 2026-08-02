from dataclasses import dataclass

from hindsight.datahub.mcp_client import DataHubMCP
from hindsight.models import InvestigationState


@dataclass
class Ctx:
    state: InvestigationState
    datahub: DataHubMCP
