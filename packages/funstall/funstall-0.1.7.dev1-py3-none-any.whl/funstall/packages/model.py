from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel as _BaseModel
from pydantic import (
    ConfigDict,
    Field,
)


class BaseModel(_BaseModel):
    model_config = ConfigDict(extra="forbid")


class PackageData(BaseModel):
    version: int
    packages: list[Package]


class Package(BaseModel):
    name: str
    sources: list[PackageSource]
    dependencies: list[Dependency] | None = None


type PackageSource = Annotated[
    PacmanDef | PipDef | NpmDef | BrewDef | NuDef, Field(discriminator="kind")
]


class BaseSource(BaseModel):
    condition: Condition | None = None


class PipDef(BaseSource):
    kind: Literal["pip"]
    config: PipConfig


class PipConfig(BaseModel):
    name: str
    python_version: str
    executables: list[str]


class NpmDef(BaseSource):
    kind: Literal["npm"]
    config: NpmConfig


class NpmConfig(BaseModel):
    name: str
    node_version: str
    executables: list[str]
    additional_packages: list[str] | None = None


class PacmanDef(BaseSource):
    kind: Literal["pacman"]
    config: PacmanConfig


class PacmanConfig(BaseModel):
    name: str


class BrewDef(BaseSource):
    kind: Literal["brew"]
    config: BrewConfig


class BrewConfig(BaseModel):
    name: str


class NuDef(BaseSource):
    kind: Literal["nushell-script"]
    config: NuConfig


class NuConfig(BaseModel):
    installation: ScriptConfig
    update: ScriptConfig


class ScriptConfig(BaseModel):
    elevated_priviliges: bool = False
    source_file: Path


class Dependency(BaseModel):
    name: str
    condition: Condition | None = None


class PackageManagerCondition(BaseModel):
    kind: Literal["package-manager"]
    is_: str = Field(alias="is")


class DisplayServerCondition(BaseModel):
    kind: Literal["display-server"]
    is_: str = Field(alias="is")


type Condition = Annotated[
    PackageManagerCondition | DisplayServerCondition,
    Field(discriminator="kind"),
]


class PackageError(Exception):
    pass


class InvalidPackageFileError(PackageError):
    pass
