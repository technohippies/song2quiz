from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Range:
    content: str


@dataclass
class BoundingBox:
    width: int
    height: int


@dataclass
class AvatarImage:
    url: str
    bounding_box: BoundingBox


@dataclass
class Avatar:
    tiny: AvatarImage
    thumb: AvatarImage
    small: AvatarImage
    medium: AvatarImage


@dataclass
class UserMetadata:
    permissions: List[str]
    excluded_permissions: List[str]
    interactions: Dict[str, bool]


@dataclass
class User:
    api_path: str
    avatar: Avatar
    header_image_url: str
    human_readable_role_for_display: str
    id: int
    iq: int
    login: str
    name: str
    role_for_display: str
    url: str
    current_user_metadata: UserMetadata


@dataclass
class Author:
    attribution: float
    pinned_role: Optional[str]
    user: User


@dataclass
class IQAction:
    primary: Dict[str, Any]


@dataclass
class AnnotationMetadata:
    permissions: List[str]
    excluded_permissions: List[str]
    interactions: Dict[str, bool]
    iq_by_action: Dict[str, IQAction]


@dataclass
class DOMNode:
    tag: str
    children: List[Any]  # Can be either strings or more DOMNodes


@dataclass
class AnnotationBody:
    dom: DOMNode


@dataclass
class Annotation:
    api_path: str
    body: AnnotationBody
    comment_count: int
    community: bool
    custom_preview: Optional[str]
    has_voters: bool
    id: int
    pinned: bool
    share_url: str
    source: Optional[str]
    state: str
    url: str
    verified: bool
    votes_total: int
    current_user_metadata: AnnotationMetadata
    authors: List[Author]
    cosigned_by: List[Any]
    rejection_comment: Optional[str]
    verified_by: Optional[str]


@dataclass
class ClientTimestamps:
    updated_by_human_at: int
    lyrics_updated_at: int


@dataclass
class Annotatable:
    api_path: str
    client_timestamps: ClientTimestamps
    context: str
    id: int
    image_url: str
    link_title: str
    title: str
    type: str
    url: str


@dataclass
class Referent:
    _type: str
    annotator_id: int
    annotator_login: str
    api_path: str
    classification: str
    fragment: str
    id: int
    is_description: bool
    path: str
    range: Range
    song_id: int
    url: str
    verified_annotator_ids: List[int]
    annotatable: Annotatable
    annotations: List[Annotation]
