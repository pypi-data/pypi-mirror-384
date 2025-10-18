from pydantic import BaseModel, Field, constr
from typing import Literal, Optional

AccessRightsType = Literal["workspace", "company-user-groups", "company", "public"]


class SessionsConfig(BaseModel):
    path: Optional[str] = None
    persistSession: bool = True


class AppConfigs(BaseModel):
    sessions: SessionsConfig


class AppParams(BaseModel):
    sourcePath: str
    config: AppConfigs


class AppConfig(BaseModel):
    appType: Literal["hal-e"] = "hal-e"
    name: str
    accessType: AccessRightsType = "workspace"
    appParams: AppParams
    description: str = Field("", max_length=100)


class HalEPayload(BaseModel):
    appConfig: AppConfig


class HalEData(BaseModel):
    appConfig: AppConfig
    friendlyUrl: str
