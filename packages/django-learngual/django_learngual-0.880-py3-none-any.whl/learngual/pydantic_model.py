from typing import Any, Literal

from django.utils import timezone
from pydantic import AnyHttpUrl, Field, field_validator

from .interface import BaseModel, BaseTypeModel


class SocialMediaLinksSchema(BaseModel):
    facebook: AnyHttpUrl | None = Field(None)
    instagram: AnyHttpUrl | None = Field(None)
    linkedin: AnyHttpUrl | None = Field(None)
    twitter: AnyHttpUrl | None = Field(None)
    website: AnyHttpUrl | None = Field(None)


"""
Account settings link
"""


class AccountSettingsSchema:
    class Base(BaseTypeModel):
        type: Literal["DEFAULT"] = "DEFAULT"
        social_links: SocialMediaLinksSchema = Field(
            default_factory=SocialMediaLinksSchema
        )

    class EnterpriseSettings(Base, BaseTypeModel):

        type: Literal["ENTERPRISE"] = "ENTERPRISE"
        who_can_view_your_profile: Literal[
            "Enterprise members only",
            "Enterprise members and public viewers",
            "Public viewers",
        ] = Field("Enterprise members only")
        show_statistics: bool = Field(False)
        show_available_course_languages: bool = Field(False)
        show_social_media_links: bool = Field(False)
        show_courses: bool = Field(False)

    class InstructorSettings(Base):
        type: Literal["INSTRUCTOR"] = "INSTRUCTOR"
        who_can_view_your_profile: Literal[
            "Friends",
            "Students only",
            "Instructors only",
            "Students and instructors",
            "All enterprise",
        ] = Field("Friends")
        show_statistics: bool = Field(True)
        show_available_course_languages: bool = Field(True)
        show_social_media_links: bool = Field(True)
        show_courses: bool = Field(True)
        show_affiliates: bool = Field(True)

    class PersonalSettings(Base):
        who_can_view_your_profile: Literal[
            "Friends",
            "All affiliated accounts",
            "Public",
            "Students and enterprise",
            "Students and instructors",
        ] = Field("Friends")
        show_evaluations: bool = Field(True)
        show_achievements: bool = Field(True)
        show_affiliate: bool = Field(True)
        show_courses: bool = Field(True)
        exercises_per_week: int = Field(0)

        type: Literal["PERSONAL"] = "PERSONAL"

    class DeveloperSettings(Base):
        type: Literal["DEVELOPER"] = "DEVELOPER"


class MediaFileSchema(BaseTypeModel):
    id: str = Field("0", description="Unique identifier for the media file")
    url: str = Field(
        "https://learngual-bucket.sfo3.cdn.digitaloceanspaces.com/static/default-avatar.png",
        description="Direct URL to access the media file",
    )
    thumbnail_url: str | None = Field(
        None, description="Optional thumbnail URL for the media file"
    )
    uploaded_by: dict[str, Any] | None = Field(
        None,
        description="Information about the user who uploaded the media file",
    )
    stream_url: str | None = Field(
        None, description="Optional streaming URL for the media file"
    )
    mimetype: str = Field(
        default="image/png",
        description="MIME type of the media file (e.g., image/jpeg, video/mp4)",
    )
    size: float | int = Field(
        default=0,
        ge=0,
        description="Size of the media file in bytes. Must be a non-negative integer",
    )
    convertion_status: str | None = Field(
        None,
        description="Status of the media file conversion (e.g., 'pending', 'completed')",
    )
    duration: timezone.timedelta | None = Field(
        None, description="Duration of the media file (if applicable)"
    )
    course_count: int = Field(
        default=0,
        ge=0,
        description="Number of courses associated with the media file",
    )
    last_used: timezone.datetime | None = Field(
        None, description="Timestamp when the media file was last used"
    )
    created_at: timezone.datetime | None = Field(
        None, description="Timestamp when the media file was created"
    )
    updated_at: timezone.datetime | None = Field(
        None, description="Timestamp when the media file was last updated"
    )

    @field_validator("duration", mode="before")
    @classmethod
    def remove_space(cls, value: str | None) -> str | None:
        if value is not None:
            return value.strip()


class DeveloperProfilePhotoSchema(MediaFileSchema):
    url: str = Field(
        "https://learngual-bucket.sfo3.cdn.digitaloceanspaces.com/static/Developer.png",
        description="Direct URL to access the media file",
    )


class ProfilePhotoSchema(MediaFileSchema):
    url: str = Field(
        "https://learngual-bucket.sfo3.cdn.digitaloceanspaces.com/static/default-avatar.png",
        description="Direct URL to access the media file",
    )


class CoverPhotoSchema(MediaFileSchema):
    url: str = Field(
        "https://learngual-bucket.sfo3.cdn.digitaloceanspaces.com/static/default-cover-photo.png",
        description="Direct URL to access the media file",
    )
