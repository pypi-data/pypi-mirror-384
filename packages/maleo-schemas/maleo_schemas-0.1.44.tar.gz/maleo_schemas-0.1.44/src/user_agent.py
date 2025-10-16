from pydantic import BaseModel, Field
from typing import Annotated, Tuple
from user_agents.parsers import parse
from maleo.types.string import OptStr


class Browser(BaseModel):
    family: Annotated[str, Field(..., description="Browser's family")]
    version: Annotated[Tuple[int, ...], Field(..., description="Browser's version")]
    version_string: Annotated[str, Field(..., description="Browser's version string")]


class OperatingSystem(BaseModel):
    family: Annotated[str, Field(..., description="OS's family")]
    version: Annotated[Tuple[int, ...], Field(..., description="OS's version")]
    version_string: Annotated[str, Field(..., description="OS's version string")]


class Device(BaseModel):
    family: Annotated[str, Field(..., description="Device's family")]
    brand: Annotated[OptStr, Field(None, description="Device's brand")]
    model: Annotated[OptStr, Field(None, description="Device's model")]


class UserAgent(BaseModel):
    ua_string: Annotated[str, Field(..., description="Raw User-Agent header")]
    browser: Annotated[Browser, Field(..., description="Browser User-Agent")]
    os: Annotated[OperatingSystem, Field(..., description="OS User-Agent")]
    device: Annotated[Device, Field(..., description="Platform User-Agent")]

    is_mobile: Annotated[bool, Field(..., description="Whether is mobile")]
    is_tablet: Annotated[bool, Field(..., description="Whether is tablet")]
    is_pc: Annotated[bool, Field(..., description="Whether is PC")]
    is_bot: Annotated[bool, Field(..., description="Whether is bot")]
    is_touch_capable: Annotated[
        bool, Field(..., description="Whether is touch capable")
    ]
    is_email_client: Annotated[bool, Field(..., description="Whether is email client")]

    @classmethod
    def from_string(cls, user_agent_string: str) -> "UserAgent":
        parsed_user_agent = parse(user_agent_string)
        return cls.model_validate(parsed_user_agent, from_attributes=True)


OptUserAgent = UserAgent | None
