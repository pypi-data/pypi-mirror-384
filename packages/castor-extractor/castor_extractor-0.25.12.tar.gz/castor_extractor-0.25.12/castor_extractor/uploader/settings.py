from typing import Optional

from pydantic import UUID4, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constant import FileType
from .enums import Zone

UPLOADER_ENV_PREFIX = "CASTOR_UPLOADER_"


class UploaderSettings(BaseSettings):
    """Class holding Castor uploader attributes"""

    model_config = SettingsConfigDict(
        env_prefix=UPLOADER_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    directory_path: Optional[str] = None
    file_path: Optional[str] = None
    file_type: FileType
    source_id: UUID4
    token: str = Field(repr=False)
    zone: Optional[Zone] = Zone.EU
