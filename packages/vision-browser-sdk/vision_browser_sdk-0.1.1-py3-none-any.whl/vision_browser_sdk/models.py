# src/vision_browser_sdk/models.py

"""
This module contains all Pydantic models for the data
used in the Vision Browser API.

They provide validation, parsing, and convenient IDE auto-completion
for all requests and responses.
"""

from typing import List, Optional, Any, Dict, Generic, TypeVar
from pydantic import BaseModel, Field

# --- Generic Response Wrappers ---

DataType = TypeVar('DataType')


class VisionUsage(BaseModel):
    """Model for plan usage data."""
    users: int
    profiles: int


class VisionDataResponse(BaseModel, Generic[DataType]):
    """
    Universal wrapper for responses containing a "data" field.
    e.g., {"data": ..., "usage": ...}
    """
    data: DataType
    usage: Optional[VisionUsage] = None


# --- Folder Models ---

class Folder(BaseModel):
    """Model for a folder."""
    id: str
    owner: str
    folder_name: str = Field(alias='folder_name')
    folder_icon: str = Field(alias='folder_icon')
    folder_color: str = Field(alias='folder_color')
    created_at: str = Field(alias='created_at')
    updated_at: str = Field(alias='updated_at')
    deleted_at: Optional[str] = Field(None, alias='deleted_at')


class CreateFolderPayload(BaseModel):
    """Request body for creating a folder."""
    folder_name: str
    folder_icon: str
    folder_color: str


class UpdateFolderPayload(BaseModel):
    """Request body for updating a folder."""
    folder_name: Optional[str] = None
    folder_icon: Optional[str] = None
    folder_color: Optional[str] = None


# --- Geolocation Model (for Proxies) ---

class Geolocation(BaseModel):
    """Model for proxy geolocation information."""
    ip: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# --- Proxy Models (defined before Profile) ---

class Proxy(BaseModel):
    """Model for a proxy."""
    id: str
    user_id: Optional[str] = Field(None, alias='user_id')
    folder_id: Optional[str] = Field(None, alias='folder_id')
    proxy_name: str = Field(alias='proxy_name')
    proxy_type: str = Field(alias='proxy_type')
    proxy_ip: str = Field(alias='proxy_ip')
    proxy_port: int = Field(alias='proxy_port')
    proxy_username: Optional[str] = Field(None, alias='proxy_username')
    proxy_password: Optional[str] = Field(None, alias='proxy_password')
    update_url: Optional[str] = Field(None, alias='update_url')
    created_at: Optional[str] = Field(None, alias='created_at')
    updated_at: Optional[str] = Field(None, alias='updated_at')
    geo_info: Optional[Geolocation] = Field(None, alias='geo_info')


# --- Profile & Fingerprint Models ---

class Screen(BaseModel):
    width: int
    height: int
    pixel_ratio: float = Field(alias='pixel_ratio')
    avail_width: int = Field(alias='avail_width')
    avail_height: int = Field(alias='avail_height')
    color_depth: int = Field(alias='color_depth')


class Hints(BaseModel):
    architecture: str
    platform: str
    platform_version: str = Field(alias='platform_version')
    mobile: bool
    ua_full_version: str = Field(alias='ua_full_version')


class Navigator(BaseModel):
    hardware_concurrency: int = Field(alias='hardware_concurrency')
    device_memory: float = Field(alias='device_memory')
    user_agent: str = Field(alias='user_agent')
    platform: str
    language: str
    languages: List[str]


class Fingerprint(BaseModel):
    """Model for a browser fingerprint."""
    major: int
    os: str
    screen: Screen
    hints: Hints
    navigator: Navigator
    webgl: Dict[str, Any]
    webgpu: Dict[str, Any]
    crc: str
    fonts: List[str] = []
    webrtc_pref: str = Field(alias='webrtc_pref')
    canvas_pref: str = Field(alias='canvas_pref')
    webgl_pref: str = Field(alias='webgl_pref')


class Profile(BaseModel):
    """Model for a profile."""
    id: str
    owner: str
    folder_id: str = Field(alias='folder_id')
    proxy_id: Optional[str] = Field(None, alias='proxy_id')
    profile_name: str = Field(alias='profile_name')
    profile_notes: str = Field(alias='profile_notes')
    profile_status: Optional[Any] = Field(None, alias='profile_status')
    profile_tags: List[str] = Field(alias='profile_tags')
    browser: str
    platform: str
    running: bool
    pinned: bool
    worktime: int
    last_run_at: Optional[str] = Field(None, alias='last_run_at')
    created_at: str = Field(alias='created_at')
    updated_at: str = Field(alias='updated_at')
    proxy: Optional[Proxy] = None
    fingerprint: Optional[Fingerprint] = None

    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ: Добавлены недостающие поля ---
    recovered: int
    is_received: bool = Field(alias='is_received')
    app_version: str = Field(alias='app_version')


class ProfileList(BaseModel):
    """Data structure for a list of profiles."""
    total: int
    items: List[Profile]


class CreateProfilePayload(BaseModel):
    """Request body for creating a profile."""
    profile_name: str
    platform: str
    fingerprint: Dict[str, Any]
    profile_notes: str = ""
    profile_tags: List[str] = []
    proxy_id: Optional[str] = None
    browser: str = "Chrome"


class UpdateProfilePayload(BaseModel):
    """Request body for updating a profile."""
    profile_name: Optional[str] = None
    profile_notes: Optional[str] = None
    profile_tags: Optional[List[str]] = None
    new_profile_tags: Optional[List[str]] = None
    profile_status: Optional[str] = None
    pinned: Optional[bool] = None
    proxy_id: Optional[str] = None


class FingerprintData(BaseModel):
    """Response structure for fingerprint data."""
    fingerprint: Dict[str, Any]


# --- Cookie Models ---

class Cookie(BaseModel):
    """Model for a cookie."""
    name: str
    value: str
    path: str
    domain: str
    expires: float


class ImportCookiesPayload(BaseModel):
    """Request body for importing cookies."""
    cookies: List[Cookie]


# --- Proxy Payload Models (continued) ---

class CreateProxyItem(BaseModel):
    """A single proxy in a creation request."""
    proxy_name: str
    proxy_type: str
    proxy_ip: str
    proxy_port: int
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    update_url: Optional[str] = None


class CreateProxyPayload(BaseModel):
    """Request body for creating one or more proxies."""
    proxies: List[CreateProxyItem]


class UpdateProxyPayload(CreateProxyItem):
    """Request body for updating a proxy."""
    pass


class DeleteProxyPayload(BaseModel):
    """Request body for deleting proxies."""
    proxy_ids: List[str]


# --- Status Models ---

class Status(BaseModel):
    """Model for a status."""
    id: str
    user_id: str = Field(alias='user_id')
    folder_id: str = Field(alias='folder_id')
    status: str
    status_color: str = Field(alias='status_color')
    created_at: str = Field(alias='created_at')
    updated_at: str = Field(alias='updated_at')


class CreateStatusesPayload(BaseModel):
    statuses: List[List[str]]


class UpdateStatusPayload(BaseModel):
    name: str
    color: str


class DeleteStatusesPayload(BaseModel):
    status_ids: List[str]


# --- Tag Models ---

class Tag(BaseModel):
    """Model for a tag."""
    id: str
    user_id: str = Field(alias='user_id')
    folder_id: str = Field(alias='folder_id')
    tag_name: str = Field(alias='tag_name')
    created_at: str = Field(alias='created_at')
    updated_at: str = Field(alias='updated_at')


class CreateTagsPayload(BaseModel):
    tags: List[str]


class UpdateTagPayload(BaseModel):
    name: str


class DeleteTagsPayload(BaseModel):
    tag_ids: List[str]


# --- Local API Models ---

class RunningProfile(BaseModel):
    folder_id: str
    profile_id: str
    port: Optional[int] = None


class RunningProfileListResponse(BaseModel):
    profiles: List[RunningProfile]


class RunningProfileInfo(BaseModel):
    folder_id: str
    profile_id: str
    port: int


class TempProxy(BaseModel):
    type: str
    address: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


class StartProfilePayload(BaseModel):
    args: Optional[List[str]] = None
    proxy: Optional[TempProxy] = None
