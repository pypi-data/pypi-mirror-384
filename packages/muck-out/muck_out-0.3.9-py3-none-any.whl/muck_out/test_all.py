import pytest
import json

from zipfile import ZipFile

from muck_out.types import Object, Activity

from . import normalize_data as normalize


def object_data():
    with ZipFile("test_data/samples.zip") as zip_file:
        for file_name in zip_file.namelist():
            if file_name.startswith("object/"):
                yield file_name, json.loads(zip_file.read(file_name))


def activity_data():
    with ZipFile("test_data/samples.zip") as zip_file:
        for file_name in zip_file.namelist():
            if file_name.startswith("activity/"):
                yield file_name, json.loads(zip_file.read(file_name))


failing_objects = [
    "object/object_types_12.json",
    "object/object_types_13.json",
    "object/necessary_properties_1.json",
    "object/necessary_properties_3.json",
    "object/necessary_properties_4.json",
    # "object/in_reply_to_4.json",
    # "object/attributed_to_2.json",
]


@pytest.mark.parametrize("file_name, data", object_data())
def test_objects(file_name, data):
    normalized = normalize(data)

    if file_name in failing_objects:
        assert normalized.object is None
    else:
        assert normalized.object

        dumped = normalized.object.model_dump()
        Object(**dumped)


@pytest.mark.parametrize("file_name, data", activity_data())
def test_activities(file_name, data):
    normalized = normalize(data)

    assert normalized.activity

    dumped = normalized.activity.model_dump()
    Activity(**dumped)


def actor_data():
    with ZipFile("test_data/funfedi-samples.zip") as zip_file:
        for file_name in zip_file.namelist():
            if file_name.startswith("actors/"):
                yield file_name, json.loads(zip_file.read(file_name))


@pytest.mark.parametrize("file_name, data", actor_data())
def test_actors(file_name, data):
    normalized = normalize(data)

    assert normalized.actor
