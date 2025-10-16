import logging
from collections.abc import Generator
from contextlib import contextmanager
from random import choice
from typing import Any, TypedDict
from unittest.mock import MagicMock, patch
from uuid import uuid4

from faker import Faker

from ..utils import (
    PermissionManager,
    PermissonUtils,
    flatten_dict,
    get_nested_value,
    unflatten_dict,
    update_nested_value,
)
from .request_mock import requests

faker = Faker()


def test_update_nested_value():
    permission_data: dict = dict(
        metadata=dict(
            request_count=dict(
                value=faker.pyint(min_value=100, max_value=1000),
            ),
            manage_courses=dict(value=faker.pybool()),
            ids=[0, 1, 2, 3, 4, 5, 6],
            age=10,
        ),
    )
    res = update_nested_value(permission_data, "metadata.age", 20)
    assert res.get("metadata", {}).get("age") == 20
    assert permission_data.get("metadata", {}).get("age") == 20


def test_flatten_dict():
    permission_data: dict = dict(
        metadata=dict(
            request_count=dict(
                value=faker.pyint(min_value=100, max_value=1000),
            ),
            manage_courses=dict(value=faker.pybool()),
            ids=[0, 1, 2, 3, 4, 5, 6],
        ),
    )
    permission_data_flat = {
        "metadata.request_count.value": permission_data.get("metadata", {})
        .get("request_count", {})
        .get("value"),
        "metadata.manage_courses.value": permission_data.get("metadata", {})
        .get("manage_courses", {})
        .get("value"),
        "metadata.ids": permission_data.get("metadata", {}).get("ids"),
    }
    assert flatten_dict(permission_data) == permission_data_flat
    assert unflatten_dict(permission_data_flat) == permission_data


def test_get_nested_value():
    permission_data: dict = dict(
        metadata=dict(
            request_count=dict(
                value=faker.pyint(min_value=100, max_value=1000),
            ),
            manage_courses=dict(value=faker.pybool()),
            ids=[0, 1, 2, 3, 4, 5, 6],
        ),
    )
    assert get_nested_value(permission_data, "metadata.request_count.value")
    assert not get_nested_value(permission_data, "metadata.request_count.val")
    assert get_nested_value(permission_data, "metadata.request_count")
    assert (
        get_nested_value(permission_data, "metadata.ids[1]")
        == permission_data.get("metadata", {}).get("ids")[1]
    )
    assert (
        get_nested_value(permission_data, "metadata.ids[0:4]")
        == permission_data.get("metadata", {}).get("ids")[0:4]
    )


def test_PermissonUtils():
    permission_data: dict = dict(
        metadata=dict(
            request_count=dict(
                value=faker.pyint(min_value=100, max_value=1000),
            ),
            manage_courses=dict(value=faker.pybool()),
            value=20,
        ),
    )
    permission: PermissonUtils = PermissonUtils(permission_data)
    assert permission.bool("metadata.manage_courses.value") == permission_data.get(
        "metadata", {}
    ).get("manage_courses", {}).get("value")

    assert type(permission.bool("metadata.manage_courses.value")) == bool
    assert permission.bool("metadata.manage_courses.alue") is None

    assert permission.int("metadata.request_count.value") == permission_data.get(
        "metadata", {}
    ).get("request_count", {}).get("value")

    assert type(permission.int("metadata.request_count.value")) == int
    assert permission.int("metadata.request_count.alue") == int()

    assert type(permission.float("metadata.request_count.value")) == float

    # check increment works
    value = faker.pyint(min_value=1, max_value=100)
    res = permission.add_number("metadata.value", value)
    assert res.get("metadata", {}).get("value") == 20 + value

    # check that decrement works
    res = permission.add_number("metadata.value", -30)
    assert res.get("metadata", {}).get("value") == 20 + value - 30

    # check that error is raised if key does not exist
    try:
        permission.add_number("metadata.fake", -30)
        assert False, "did not raise key error"
    except KeyError:
        assert True

    # check that error is raised for wrong type
    try:
        permission.add_number("metadata.value", "334459aas")
        assert False, "did not raise type error"
    except TypeError:
        assert True

    # check that force create works
    assert permission.add_number("metadata.fake", -30, force_create=True)

    # check that force create works
    assert permission.set_value("metadata.fake2", -30, force_create=True)
    permission.set_value("metadata.value", -30)
    assert permission.to_dict().get("metadata", {}).get("value") == -30

    try:
        permission.set_value("metadata.fake4", -30)
        assert False
    except KeyError:
        assert True

    permission_data: dict = dict(
        metadata=dict(
            request_count=dict(
                value=faker.pyint(min_value=100, max_value=1000),
            ),
            manage_courses=dict(value=faker.pybool()),
            ids=[0, 1, 2, 3, 4, 5, 6],
        ),
    )
    permission_data_flat = {
        "metadata.request_count.value": permission_data.get("metadata", {})
        .get("request_count", {})
        .get("value"),
        "metadata.manage_courses.value": permission_data.get("metadata", {})
        .get("manage_courses", {})
        .get("value"),
        "metadata.ids": permission_data.get("metadata", {}).get("ids"),
    }
    assert PermissonUtils(permission_data).to_flat_dict() == permission_data_flat
    assert PermissonUtils(permission_data).to_dict() == permission_data


@patch("iam_service.learngual.utils.requests.get", return_value=requests.get)
def test_permission_manager(mock_requests):
    permission_manager: PermissionManager = PermissionManager()
    permission_flat_dict = {
        "metadata.request_count.value": 100000,
        "metadata.messages.value": True,
        "metadata.analytics.value": False,
    }
    permission_dict = unflatten_dict(permission_flat_dict)
    assert not permission_dict.get("metadata.request_count.value")
    mock_requests.return_value.json.return_value = permission_dict
    random_key = choice(list(permission_flat_dict.keys()))
    res = permission_manager.retrieve_permission(
        base_url="https://example.com", permission_id=uuid4().hex[:10], service="iam"
    )
    assert res == permission_dict, res
    res = permission_manager.retrieve_permission(
        base_url="https://example.com",
        permission_id=uuid4().hex[:10],
        service="iam",
        dot_path=random_key,
    )
    assert res == permission_flat_dict.get(random_key), res


class MetadataValue(TypedDict):
    value: Any
    state: str | None


class PermissionMetadata(TypedDict):
    is_free: MetadataValue
    subscription_expired: MetadataValue
    unlimited_course_creation: MetadataValue
    manage_course_instructor_and_student: MetadataValue
    custom_lesson_creation: MetadataValue
    reports: MetadataValue
    ai_powered_student_grading: MetadataValue
    word_sentence_language_translation: MetadataValue
    access_to_learngual_features: MetadataValue
    modular_learning_exercise: MetadataValue
    announcements: MetadataValue
    access_conversational_ai_lesson_structure: MetadataValue
    access_student_learning_progress: MetadataValue
    access_instructor_progress: MetadataValue
    storage: MetadataValue
    enterprise_user_group_size: MetadataValue
    grace_period_ended: MetadataValue


class PermissionData(TypedDict):
    metadata: PermissionMetadata


@contextmanager
def mock_permission_context(
    permission_data: PermissionData | None = None,
) -> Generator[MagicMock, None, None]:
    with patch("learngual.utils.requests.get") as mock_dependency:
        try:
            mock_dependency.return_value.json.return_value = permission_data or {
                "metadata": {
                    "is_free": {"value": True},
                    "subscription_expired": {"value": False, "state": "ACTIVE"},
                    "unlimited_course_creation": {"value": True},
                    "manage_course_instructor_and_student": {"value": True},
                    "custom_lesson_creation": {"value": True},
                    "reports": {"value": True},
                    "ai_powered_student_grading": {"value": True},
                    "word_sentence_language_translation": {"value": True},
                    "access_to_learngual_features": {"value": True},
                    "modular_learning_exercise": {"value": True},
                    "announcements": {"value": True},
                    "access_conversational_ai_lesson_structure": {"value": True},
                    "access_student_learning_progress": {"value": True},
                    "access_instructor_progress": {"value": True},
                    "storage": {"value": 5000000},  # this is in bytes
                    "enterprise_user_group_size": {"value": 1000},
                    "grace_period_ended": {"value": False},
                }
            }

            yield mock_dependency
        finally:
            logging.warning("Error occurred")
