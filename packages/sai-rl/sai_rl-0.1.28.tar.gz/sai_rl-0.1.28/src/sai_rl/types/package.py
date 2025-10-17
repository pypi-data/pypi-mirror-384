from pydantic import BaseModel


class PackageType(BaseModel):
    id: str
    name: str
    version: str
