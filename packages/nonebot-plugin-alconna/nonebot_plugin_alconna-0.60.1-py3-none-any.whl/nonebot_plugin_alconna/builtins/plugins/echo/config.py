from pydantic import BaseModel, Field


class Config(BaseModel):
    """Plugin Config Here"""

    nbp_alc_echo_tome: bool = Field(default=False)
