from pydantic import BaseModel
from typing import Optional


class Profile(BaseModel):
    UserID: Optional[int] = None
    Title: Optional[str] = None
    UserEmail: Optional[str] = None
    UserPhone: Optional[str] = None
    Description: Optional[str] = None
    EmailVerified: Optional[str] = "NO"
    PhoneVerified: Optional[str] = "NO"
    UserPassword: Optional[str] = None
    ActiveFlags: Optional[str] = "INACTIVE"
    UserIdentifier: Optional[str] = None
    ProfilePic: Optional[str] = None
    Location: Optional[str] = None
    Longitude: Optional[float] = None
    Latitude: Optional[float] = None
    IMEI: Optional[str] = None


class Attribute(BaseModel):
    # UserID: Optional[int] = None
    AttributeID: Optional[int] = None
    key: Optional[str] = "NO"
    value: Optional[list] = []
    isUser: Optional[bool] = False


class User(BaseModel):
    Profile: Profile
    Attributes: Optional[list[Attribute]] = []
    SendEmailSMSOnUserCreation: Optional[bool] = True
    Groups: Optional[list] = []
    EncryptedZviceID: Optional[str] = None
    ParentGroups: Optional[list] = []
