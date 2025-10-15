from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import dataclasses


@dataclass
class DashboardOrganizationsCreateOutput:
  object: str
  id: str
  status: str
  type: str
  slug: str
  name: str
  organization_id: str
  image_url: str
  created_at: datetime
  updated_at: datetime


class mapDashboardOrganizationsCreateOutput:
  @staticmethod
  def from_dict(data: Dict[str, Any]) -> DashboardOrganizationsCreateOutput:
    return DashboardOrganizationsCreateOutput(
      object=data.get("object"),
      id=data.get("id"),
      status=data.get("status"),
      type=data.get("type"),
      slug=data.get("slug"),
      name=data.get("name"),
      organization_id=data.get("organization_id"),
      image_url=data.get("image_url"),
      created_at=datetime.fromisoformat(data.get("created_at"))
      if data.get("created_at")
      else None,
      updated_at=datetime.fromisoformat(data.get("updated_at"))
      if data.get("updated_at")
      else None,
    )

  @staticmethod
  def to_dict(
    value: Union[DashboardOrganizationsCreateOutput, Dict[str, Any], None]
  ) -> Optional[Dict[str, Any]]:
    if value is None:
      return None
    if isinstance(value, dict):
      return value
    # assume dataclass for generated models
    return dataclasses.asdict(value)


@dataclass
class DashboardOrganizationsCreateBody:
  name: str


class mapDashboardOrganizationsCreateBody:
  @staticmethod
  def from_dict(data: Dict[str, Any]) -> DashboardOrganizationsCreateBody:
    return DashboardOrganizationsCreateBody(name=data.get("name"))

  @staticmethod
  def to_dict(
    value: Union[DashboardOrganizationsCreateBody, Dict[str, Any], None]
  ) -> Optional[Dict[str, Any]]:
    if value is None:
      return None
    if isinstance(value, dict):
      return value
    # assume dataclass for generated models
    return dataclasses.asdict(value)
