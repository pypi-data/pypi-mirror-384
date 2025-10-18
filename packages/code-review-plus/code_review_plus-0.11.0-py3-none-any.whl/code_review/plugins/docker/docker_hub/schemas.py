from __future__ import annotations

import re

from pydantic import BaseModel


class Image(BaseModel):
    architecture: str
    features: str
    variant: str | None
    digest: str | None = None
    os: str
    os_features: str
    os_version: str | None
    size: int
    status: str
    last_pulled: str | None = None
    last_pushed: str | None = None


class ImageTag(BaseModel):
    creator: int
    id: int
    images: list[Image]
    last_updated: str
    last_updater: int
    last_updater_username: str
    name: str
    repository: int
    full_size: int
    v2: bool
    tag_status: str
    tag_last_pulled: str | None
    tag_last_pushed: str
    media_type: str | None = None
    content_type: str | None = None
    digest: str | None = None
    version: tuple[int, ...] | None = None

    def set_version(self) -> None:
        regex = r"(?<version>\d+\.\d+\.?\d*?)-(.+)"
        regexp = re.compile(regex)
        match = regexp.match(self.name)
        if match:
            version_str = match.group("version")
            self.version = tuple(int(part) for part in version_str.split("."))
        else:
            self.version = None
