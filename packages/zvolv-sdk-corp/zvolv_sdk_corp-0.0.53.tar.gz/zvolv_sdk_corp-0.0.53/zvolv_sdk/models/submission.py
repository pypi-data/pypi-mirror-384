from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class Element(BaseModel):
    id: Optional[str] = None
    elementId: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    defaultValue: Optional[Union[str, bool, int, dict, list]] = None
    value: Optional[Union[str, bool, int, dict, list]] = None
    required: Optional[bool] = False
    disabled: Optional[bool] = False
    hidden: Optional[bool] = False
    unique: Optional[bool] = False
    updateIfUnique: Optional[bool] = False
    properties: Optional[dict] = {}
    attributes: Optional[dict] = {}
    dependencies: Optional[List] = []
    validations: Optional[List] = []
    dataType: Optional[str] = None
    showLabel: Optional[bool] = True
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class Submission(BaseModel):
    id: Optional[str] = None
    uuid: Optional[str] = None
    formId: Optional[str] = None
    schemaVersion: Optional[str] = None
    allowDraft: Optional[bool] = False
    setDraftInterval: Optional[int] = None
    createdBy: Optional[int] = None
    modifiedBy: Optional[int] = None
    modifiedAt: Optional[str] = None
    generatedAt: Optional[str] = None
    configurations: Optional[dict] = {}
    elements: List[Element] = []


class LegacyElement(BaseModel):
    FormMetaID: int
    ElementType: Optional[str] = None
    FieldLabel: Optional[str] = None
    Value: Optional[Any] = None
    DefaultValue: Optional[Any] = None
    MetaData: Optional[Dict[str, Any]] = None
 
class LegacySubmission(BaseModel):
    ZviceID: str
    FormID: int
    FormSubmissionID: Optional[int] = None
    Flags: Optional[int] = 3
    MetaData: Optional[Any] = None 
    OverrideMetaData: Optional[bool] = False
    RunPySync: Optional[bool] = False
    submitDateFromApp: Optional[str] = None
    saveOffline: Optional[bool] = None
    Elements: List[LegacyElement]