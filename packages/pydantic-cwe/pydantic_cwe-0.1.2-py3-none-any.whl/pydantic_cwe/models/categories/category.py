from pydantic import Field
from typing import List, Optional, Dict, Any

from ..common import CommonBase


class Relationship(CommonBase):
    cwe_id: str = Field(..., alias="CWE_ID")
    view_id: Optional[str] = Field(None, alias="View_ID")


class Relationships(CommonBase):
    has_member: List[Relationship] = Field(default_factory=list, alias="Has_Member")


class Submission(CommonBase):
    submission_name: str = Field(..., alias="Submission_Name")
    submission_organization: str = Field(..., alias="Submission_Organization")
    submission_date: str = Field(..., alias="Submission_Date")
    submission_version: str = Field(..., alias="Submission_Version")
    submission_releasedate: str = Field(..., alias="Submission_ReleaseDate")


class Modification(CommonBase):
    modification_name: str = Field(..., alias="Modification_Name")
    modification_organization: str = Field(..., alias="Modification_Organization")
    modification_date: str = Field(..., alias="Modification_Date")
    modification_comment: Optional[str] = Field(None, alias="Modification_Comment")


class Category(CommonBase):
    id: str = Field(..., alias="ID")
    name: str = Field(..., alias="Name")
    status: str = Field(..., alias="Status")
    summary: Optional[str] = Field(None, alias="Summary")
    relationships: Optional[Dict[str, Any]] = Field(None, alias="Relationships")
    references: Optional[Dict[str, Any]] = Field(None, alias="References")
    mapping_notes: Optional[Dict[str, Any]] = Field(None, alias="Mapping_Notes")
    content_history: Optional[Dict[str, Any]] = Field(None, alias="Content_History")

    def get_weakness_ids(self) -> List[int]:
        if not self.relationships:
            return []

        cwe_ids = []

        for values in self.relationships.values():
            if isinstance(values, dict):
                values = [values]

            for member in values:
                cwe_ids.append(int(member["CWE_ID"]))

        return cwe_ids
