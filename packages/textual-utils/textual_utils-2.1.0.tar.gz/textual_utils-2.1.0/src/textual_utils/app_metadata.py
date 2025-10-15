from dataclasses import dataclass


@dataclass(frozen=True)
class AppMetadata:
    name: str
    version: str
    icon: str
    description: str
    author: str
    email: str
