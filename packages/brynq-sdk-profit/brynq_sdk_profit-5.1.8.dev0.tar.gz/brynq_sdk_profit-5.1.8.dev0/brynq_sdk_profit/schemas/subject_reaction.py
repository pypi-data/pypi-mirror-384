import pandera as pa
from pandera.typing import Series, DateTime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

#KnSubjectReaction
class VisibilityEnum(str, Enum):
    """Enum for reaction visibility"""
    INTERNAL = "I"  # Intern
    EXTERNAL_INTERNAL = "El"  # Extern en intern


class EmojiEnum(str, Enum):
    """Enum for emoji names"""
    THUMBSUP = "thumbsup"
    THUMBSDOWN = "thumbsdown"
    BLUSH = "blush"
    PARTY = "party"
    HEART = "heart"
    EYES = "eyes"


class FileAttachment(BaseModel):
    """Schema for file attachment with filename, mimetype, and filedata"""
    filename: str = Field(..., description="Name of the file")
    mimetype: str = Field(..., description="MIME type of the file (e.g., 'image/jpeg', 'application/pdf')")
    filedata: str = Field(..., description="File content as base64-encoded string")

    class Config:
        from_attributes = True


class KnReactionAttachment(BaseModel):
    """Schema for reaction attachment"""
    file_name: str = Field(..., description="FileName")
    file_id: Optional[str] = Field(None, description="File Id")
    file_stream: bytes = Field(..., description="File as byte-array")

    class Config:
        from_attributes = True


class KnReactionLabel(BaseModel):
    """Schema for reaction label"""
    sl_id: int = Field(..., description="Label")

    class Config:
        from_attributes = True


class KnReactionEmoji(BaseModel):
    """Schema for reaction emoji"""
    em_na: EmojiEnum = Field(..., description="Emoji naam thumbsup = thumbsup; thumbsdown = thumbsdown; blush = blush; party = party; heart = heart; eyes = eyes")

    class Config:
        from_attributes = True


class KnReaction(BaseModel):
    """Pydantic schema for KnReaction; connector KnSubjectReaction"""

    # Required Fields (marked with *)
    id: Optional[int] = Field(None, description="Id reactie")
    sb_id: int = Field(..., description="Dossieritem")  # Required field
    sb_tx: bytes = Field(..., description="Reactie")  # Required field
    va_re: VisibilityEnum = Field(..., description="Reactie zichtbaar I = Intern; El = Extern en intern")  # Required field
    rt_id: Optional[int] = Field(None, description="Reactie op")

    # Objects array containing attachments, labels, and emojis
    objects: Optional[List[KnReactionAttachment | KnReactionLabel | KnReactionEmoji]] = Field(default_factory=list, description="Array of reaction objects")

    class Config:
        from_attributes = True

#KnSubjectConnector
# AFAS documentation specifies ISO 8601 format for datetime fields.
class CustomBase(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        # This is needed to allow aliases like '@SbId'.
        populate_by_name = True

# Subject Schemas for Sub-Objects
class KnSubjectLinkFields(CustomBase):
    """Fields for a linked item (sub-object)."""
    sf_tp: int = Field(..., description="Soort bestemming", alias="SfTp")
    sf_id: str = Field(..., description="Id bestemming", alias="SfId")


class KnSubjectLinkElement(CustomBase):
    """Element structure for a linked item."""
    fields: KnSubjectLinkFields = Field(..., alias="Fields")

class KnSubjectLink(CustomBase):
    """Represents a single linked item object."""
    element: KnSubjectLinkElement = Field(..., alias="Element")

class KnSubjectAttachmentFields(CustomBase):
    """Fields for an attachment (sub-object)."""
    file_name: str = Field(..., description="FileName")
    file_id: Optional[str] = Field(None, description="File Id")
    file_stream: bytes = Field(..., description="File as byte-array")

class KnSubjectAttachmentElement(CustomBase):
    """Element structure for an attachment."""
    fields: KnSubjectAttachmentFields = Field(..., alias="Fields")

class KnSubjectAttachment(CustomBase):
    """Represents a single attachment object."""
    element: KnSubjectAttachmentElement = Field(..., alias="Element")

class Objects(CustomBase):
    """Container for sub-objects like links and attachments."""
    # Why: The API expects a list of attachments.
    kn_subject_attachment: Optional[List[KnSubjectAttachment]] = Field(None, alias="KnSubjectAttachment")
    # Why: The API expects a list of links.
    kn_subject_link: Optional[List[KnSubjectLink]] = Field(None, alias="KnSubjectLink")

# Main Subject Schemas
class KnSubjectFields(CustomBase):
    """Contains the fields of the dossier item to be updated."""
    st: Optional[bool] = Field(None, description="Afgehandeld", alias="St")                #boolean to mark the dossier item as completed.
    dt_st: Optional[datetime] = Field(None, description="Datum afgehandeld", alias="DtSt") #sets the completion date.
    additional_fields: Dict[str, Any] = Field(default_factory=dict)                        #Allows for sending any other field without explicitly defining it in the schema.
    class Config:
        from_attributes = True


class KnSubjectElement(CustomBase):
    """The main 'Element' that holds the dossier item's data."""
    #'@SbId' is the unique identifier for the dossier item being updated. The '@' prefix is an API requirement.
    sb_id: int = Field(..., description="Dossieritem", alias="@SbId")
    fields: Optional[KnSubjectFields] = Field(None, alias="Fields")
    # Contains sub-objects like attachments or links to be added to the dossier item.
    objects: Optional[Objects] = Field(None, alias="Objects")
    class Config:
        from_attributes = True

class KnSubjectWrapper(CustomBase):
    """This class provides the required 'Element' wrapper."""
    # Why: The entire dossier item's data must be nested under an 'Element' key.
    element: KnSubjectElement = Field(..., alias="Element")

class KnSubjectPutSchema(CustomBase):
    """The root schema for a KnSubject PUT request."""
    #entire payload must be nested under the 'KnSubject' key.
    kn_subject: KnSubjectWrapper = Field(..., alias="KnSubject")

    class Config:
        from_attributes = True
