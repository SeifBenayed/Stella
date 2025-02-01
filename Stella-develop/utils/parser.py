from pydantic import BaseModel, Field


class GetLink(BaseModel):
    link: str = Field(description="link parsed from the website")