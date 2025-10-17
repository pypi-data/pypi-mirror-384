from typing import Any

from pydantic import Field

from albert.core.base import BaseAlbertModel
from albert.core.shared.identifiers import BTDatasetId
from albert.core.shared.models.base import BaseResource, EntityLink


class BTDatasetReferences(BaseAlbertModel):
    project_ids: list[str]
    data_column_ids: list[str]
    sheet_ids: list[str] | None = Field(default=None)
    filter: dict[str, Any] | None = Field(default=None)


class BTDataset(BaseResource):
    name: str
    id: BTDatasetId | None = Field(default=None, alias="albertId")
    key: str | None = Field(default=None)
    file_name: str | None = Field(default=None, alias="fileName")
    report: EntityLink | None = Field(default=None, alias="Report")
    references: BTDatasetReferences | None = Field(default=None, alias="References")
