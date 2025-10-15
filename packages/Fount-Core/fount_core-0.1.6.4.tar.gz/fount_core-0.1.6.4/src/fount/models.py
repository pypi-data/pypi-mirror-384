import os
# import httpx
from pydantic import  Field, SecretStr
from pydantic.main import BaseModel



class Config(BaseModel):
    fount_base_url: str = Field(alias="base_url",
        default=os.getenv("FOUNT_BASE_URL","https://fountondev.datapoem.ai/api/v1/"))
    fount_api_key: SecretStr = Field(alias="api_key",
            default_factory=lambda: SecretStr(os.getenv("FOUNT_API_KEY", ""))
        )
    timeout: float = 200.0
