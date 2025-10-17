from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class Task(BaseModel):
    id: Optional[int] = None
    uuid: Optional[str] = None
    submissionId: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    duration: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    priority: Optional[str] = None
    escalationToL1Duration: Optional[str] = None
    escalationToL2Duration: Optional[str] = None
    escalationToL3Duration: Optional[str] = None
    activation: Optional[str] = None
    labels: Optional[List] = []
    progressPercent: Optional[int] = None
    assigneeUserIds: Optional[List] = []
    assigneeRoleIds: Optional[List] = []
    escalationL1UserIds: Optional[List] = []
    escalationL1RoleIds: Optional[List] = []
    escalationL2UserIds: Optional[List] = []
    escalationL2RoleIds: Optional[List] = []
    escalationL3UserIds: Optional[List] = []
    escalationL3RoleIds: Optional[List] = []
    onBehalfOf: Optional[int] = None
    workflowId: Optional[int] = None
    workflowTypeId: Optional[int] = None

class TaskLabel(BaseModel):
    fieldLabel: str
    value: str
    color: str
    
class LegacyTask(BaseModel):
    taskID: int
    title: Optional[str] = None
    status: Optional[str] = None
    statusColor: Optional[str] = None
    priority: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    originalstartDate: Optional[str] = None
    originalendDate: Optional[str] = None
    description: Optional[str] = None
    createdAt: Optional[str] = None
    modifiedAt: Optional[str] = None
    createdBy: Optional[int] = None
    modifiedBy: Optional[int] = None
    duration: Optional[int] = None
    escalationDelay: Optional[int] = None
    currentEscalationLevel: Optional[str] = None
    projectTitle: Optional[str] = None
    reverseDependencyReference: Optional[str] = None
    reverseDependencyDuration: Optional[int] = None
    manualdates: Optional[bool] = None
    wip: Optional[bool] = None
    progressPercent: Optional[int] = None
    subTitle: Optional[str] = None
    taskType: Optional[str] = None
    labels: Optional[List[TaskLabel]] = None
    UserGroupIDLevel1: Optional[int] = None
    UserGroupIDLevel2: Optional[int] = None
    UserGroupIDLevel3: Optional[int] = None
    assignedUserGroup: Optional[str] = None
    escalationLevel1UserGroup: Optional[str] = None
    escalationLevel2UserGroup: Optional[str] = None
    escalatedUserGroup: Optional[str] = None
    nextStages: Optional[List[Any]] = None
    previousStages: Optional[List[Any]] = None
    taskMetaData: Optional[Dict[str, Any]] = None
    actions: Optional[List[Any]] = None
    content: Optional[str] = None
    FormSubmissionID: Optional[int] = None
    logs: Optional[List[Any]] = None

class LegacyTaskRequestBody(BaseModel):
    TaskID: Optional[int] = None
    Title: Optional[str] = None
    Description: Optional[str] = None
    StartDate: Optional[str] = None
    OriginalStartDate: Optional[str] = None
    OriginalEndDate: Optional[str] = None
    EndDate: Optional[str] = None
    Duration: Optional[int] = None
    EscalationDelay: Optional[int] = None
    Status: Optional[str] = None
    MidgardSubmissionID: Optional[Any] = None
    Priority: Optional[str] = None
    UserGroupIDLevel1: Optional[Any] = None
    UserGroupIDLevel2: Optional[Any] = None
    UserGroupIDLevel3: Optional[Any] = None
    MetaData: Optional[Dict[str, Any]] = None
    TaskMailConfig: Optional[Dict[str, Any]] = None
    OnCompleteMailConfig: Optional[Dict[str, Any]] = None
    ManualDates: Optional[Any] = None
    ManualDateEarlyStartAllowed: Optional[Any] = None
    ReverseDependencyReference: Optional[str] = None
    ReverseDependencyDuration: Optional[int] = None
    WIP: Optional[str] = None
    TaskType: Optional[str] = None
    WaitForAll: Optional[str] = None
    RevertOnSubmission: Optional[str] = None
    CompleteOnFSManualOrBot: Optional[str] = None
    IgnoreDependency: Optional[str] = None
    PreviousStages: Optional[List[Any]] = None
    NextStages: Optional[List[Any]] = None
    NextConfig: Optional[Dict[str, Any]] = None
    NextTasks: Optional[Dict[str, Any]] = None
    ProgressPercent: Optional[int] = None
    SubTitle: Optional[str] = None
    Department: Optional[str] = None
    form_id: Optional[str] = None
    WorkflowID: Optional[str] = None