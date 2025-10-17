from enum import Enum

from pydantic import Field

from albert.core.base import BaseAlbertModel


class AccessControlLevel(str, Enum):
    """The fine grain control"""

    PROJECT_OWNER = "ProjectOwner"
    PROJECT_EDITOR = "ProjectEditor"
    PROJECT_VIEWER = "ProjectViewer"
    PROJECT_ALL_TASKS = "ProjectAllTask"
    PROJECT_STRICT_VIEWER = "ProjectStrictViewer"
    PROJECT_PROPERTY_TASKS = "ProjectPropertyTask"
    INVENTORY_OWNER = "InventoryOwner"
    INVENTORY_VIEWER = "InventoryViewer"
    CUSTOM_TEMPLATE_OWNER = "CustomTemplateOwner"
    CUSTOM_TEMPLATE_VIEWER = "CustomTemplateViewer"
    CAS_FULL_ACCESS = "CASFullAccess"


class ACL(BaseAlbertModel):
    """The Access Control List (ACL) for a user"""

    id: str = Field(description="The id of the user for which this ACL applies")
    fgc: AccessControlLevel | None = Field(
        default=None, description="The Fine-Grain Control Level"
    )
