from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import dataclasses


@dataclass
class ServersListingsCollectionsGetOutput:
  object: str
  id: str
  name: str
  slug: str
  description: str
  created_at: datetime
  updated_at: datetime


class mapServersListingsCollectionsGetOutput:
  @staticmethod
  def from_dict(data: Dict[str, Any]) -> ServersListingsCollectionsGetOutput:
    return ServersListingsCollectionsGetOutput(
      object=data.get("object"),
      id=data.get("id"),
      name=data.get("name"),
      slug=data.get("slug"),
      description=data.get("description"),
      created_at=datetime.fromisoformat(data.get("created_at"))
      if data.get("created_at")
      else None,
      updated_at=datetime.fromisoformat(data.get("updated_at"))
      if data.get("updated_at")
      else None,
    )

  @staticmethod
  def to_dict(
    value: Union[ServersListingsCollectionsGetOutput, Dict[str, Any], None]
  ) -> Optional[Dict[str, Any]]:
    if value is None:
      return None
    if isinstance(value, dict):
      return value
    # assume dataclass for generated models
    return dataclasses.asdict(value)
