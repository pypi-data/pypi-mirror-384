from __future__ import annotations

import json
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from uuid import UUID

import httpx

import kleinkram.errors
from kleinkram._version import __version__
from kleinkram.api.client import CLI_VERSION_HEADER
from kleinkram.api.client import AuthenticatedClient
from kleinkram.api.deser import FileObject
from kleinkram.api.deser import MissionObject
from kleinkram.api.deser import ProjectObject
from kleinkram.api.deser import _parse_file
from kleinkram.api.deser import _parse_mission
from kleinkram.api.deser import _parse_project
from kleinkram.api.pagination import paginated_request
from kleinkram.api.query import FileQuery
from kleinkram.api.query import MissionQuery
from kleinkram.api.query import ProjectQuery
from kleinkram.api.query import file_query_is_unique
from kleinkram.api.query import mission_query_is_unique
from kleinkram.api.query import project_query_is_unique
from kleinkram.config import get_config
from kleinkram.errors import AccessDenied
from kleinkram.errors import InvalidFileQuery
from kleinkram.errors import InvalidMissionMetadata
from kleinkram.errors import InvalidMissionQuery
from kleinkram.errors import InvalidProjectQuery
from kleinkram.errors import MissionExists
from kleinkram.errors import MissionNotFound
from kleinkram.errors import MissionValidationError
from kleinkram.errors import ProjectExists
from kleinkram.errors import ProjectNotFound
from kleinkram.errors import ProjectValidationError
from kleinkram.models import File
from kleinkram.models import Mission
from kleinkram.models import Project
from kleinkram.utils import is_valid_uuid4
from kleinkram.utils import split_args

__all__ = [
    "_get_api_version",
    "_claim_admin",
    "_create_mission",
    "_create_project",
    "_update_mission",
    "_update_project",
    "_delete_files",
    "_delete_mission",
    "_delete_project",
    "get_files",
    "get_missions",
    "get_projects",
    "get_project",
    "get_mission",
    "get_file",
]


CLAIM_ADMIN = "/user/claimAdmin"
GET_STATUS = "/user/me"

UPDATE_PROJECT = "/projects"
UPDATE_MISSION = "/missions/tags"  # TODO: just metadata for now
CREATE_MISSION = "/missions/create"
CREATE_PROJECT = "/projects"


FILE_ENDPOINT = "/files"
MISSION_ENDPOINT = "/missions"
PROJECT_ENDPOINT = "/projects"

TAG_TYPE_BY_NAME = "/tag/filtered"


class Params(str, Enum):
    FILE_PATTERNS = "filePatterns"
    FILE_IDS = "fileUuids"
    MISSION_PATTERNS = "missionPatterns"
    MISSION_IDS = "missionUuids"
    PROJECT_PATTERNS = "projectPatterns"
    PROJECT_IDS = "projectUuids"


def _handle_list_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    json dumps lists
    """
    new_params = {}
    for k, v in params.items():
        if not isinstance(v, list):
            new_params[k] = v
        else:
            new_params[k] = json.dumps(v)
    return new_params


def _project_query_to_params(
    project_query: ProjectQuery,
) -> Dict[str, List[str]]:
    params = {}
    if project_query.patterns:
        params[Params.PROJECT_PATTERNS.value] = project_query.patterns
    if project_query.ids:
        params[Params.PROJECT_IDS.value] = list(map(str, project_query.ids))
    return params


def _mission_query_to_params(mission_query: MissionQuery) -> Dict[str, List[str]]:
    params = _project_query_to_params(mission_query.project_query)
    if mission_query.patterns:
        params[Params.MISSION_PATTERNS.value] = mission_query.patterns
    if mission_query.ids:
        params[Params.MISSION_IDS.value] = list(map(str, mission_query.ids))
    return params


def _file_query_to_params(file_query: FileQuery) -> Dict[str, List[str]]:
    params = _mission_query_to_params(file_query.mission_query)
    if file_query.patterns:
        params[Params.FILE_PATTERNS.value] = list(file_query.patterns)
    if file_query.ids:
        params[Params.FILE_IDS.value] = list(map(str, file_query.ids))
    return params


def get_files(
    client: AuthenticatedClient,
    file_query: FileQuery,
    max_entries: Optional[int] = None,
) -> Generator[File, None, None]:
    params = _file_query_to_params(file_query)
    response_stream = paginated_request(
        client, FILE_ENDPOINT, params=params, max_entries=max_entries
    )
    yield from map(lambda f: _parse_file(FileObject(f)), response_stream)


def get_missions(
    client: AuthenticatedClient,
    mission_query: MissionQuery,
    max_entries: Optional[int] = None,
) -> Generator[Mission, None, None]:
    params = _mission_query_to_params(mission_query)
    response_stream = paginated_request(
        client, MISSION_ENDPOINT, params=params, max_entries=max_entries
    )
    yield from map(lambda m: _parse_mission(MissionObject(m)), response_stream)


def get_projects(
    client: AuthenticatedClient,
    project_query: ProjectQuery,
    max_entries: Optional[int] = None,
    exact_match: bool = False,
) -> Generator[Project, None, None]:
    params = _project_query_to_params(project_query)
    response_stream = paginated_request(
        client,
        PROJECT_ENDPOINT,
        params=params,
        max_entries=max_entries,
        exact_match=exact_match,
    )
    yield from map(lambda p: _parse_project(ProjectObject(p)), response_stream)


def get_project(
    client: AuthenticatedClient, query: ProjectQuery, exact_match: bool = False
) -> Project:
    """\
    get a unique project by specifying a project spec
    """
    if not project_query_is_unique(query):
        raise InvalidProjectQuery(
            f"Project query does not uniquely determine project: {query}"
        )
    try:
        return next(get_projects(client, query, exact_match=exact_match))
    except StopIteration:
        raise ProjectNotFound(f"Project not found: {query}")


def get_mission(client: AuthenticatedClient, query: MissionQuery) -> Mission:
    """\
    get a unique mission by specifying a mission query
    """
    if not mission_query_is_unique(query):
        raise InvalidMissionQuery(
            f"Mission query does not uniquely determine mission: {query}"
        )
    try:
        return next(get_missions(client, query))
    except StopIteration:
        raise MissionNotFound(f"Mission not found: {query}")


def get_file(client: AuthenticatedClient, query: FileQuery) -> File:
    """\
    get a unique file by specifying a file query
    """
    if not file_query_is_unique(query):
        raise InvalidFileQuery(f"File query does not uniquely determine file: {query}")
    try:
        return next(get_files(client, query))
    except StopIteration:
        raise kleinkram.errors.FileNotFound(f"File not found: {query}")


def _mission_name_is_available(
    client: AuthenticatedClient, mission_name: str, project_id: UUID
) -> bool:
    mission_query = MissionQuery(
        patterns=[mission_name], project_query=ProjectQuery(ids=[project_id])
    )
    try:
        _ = get_mission(client, mission_query)
    except MissionNotFound:
        return True
    return False


def _validate_mission_name(
    client: AuthenticatedClient, project_id: UUID, mission_name: str
) -> None:
    if not _mission_name_is_available(client, mission_name, project_id):
        raise MissionExists(
            f"Mission with name: `{mission_name}` already exists"
            f" in project: {project_id}"
        )

    if is_valid_uuid4(mission_name):
        raise ValueError(
            f"Mission name: `{mission_name}` is a valid UUIDv4, "
            "mission names must not be valid UUIDv4's"
        )

    if mission_name.endswith(" "):
        raise ValueError(
            "A mission name cannot end with a whitespace. "
            f"The given mission name was '{mission_name}'"
        )


def _project_name_is_available(client: AuthenticatedClient, project_name: str) -> bool:
    project_query = ProjectQuery(patterns=[project_name])
    try:
        _ = get_project(client, project_query, exact_match=True)
    except ProjectNotFound:
        return True
    return False


def _validate_mission_created(
    client: AuthenticatedClient, project_id: str, mission_name: str
) -> None:
    """
    validate that a mission is successfully created
    """
    mission_ids, mission_patterns = split_args([mission_name])
    project_ids, project_patterns = split_args([project_id])

    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)
    mission_query = MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )
    try:
        with tempfile.NamedTemporaryFile(suffix=".mcap", delete=False) as tmp:
            tmp.write(b"dummy content")
            tmp_path = Path(tmp.name)

        kleinkram.core.upload(
            client=client,
            query=mission_query,
            file_paths=[tmp_path],
            verbose=False,
        )

        file_query = FileQuery(
            ids=[],
            patterns=[tmp_path.name],
            mission_query=mission_query,
        )
        file_parsed = get_file(client, file_query)

        kleinkram.core.delete_files(client=client, file_ids=[file_parsed.id])

    except Exception as e:
        raise MissionValidationError(f"Mission validation failed: {e}")

    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _create_mission(
    client: AuthenticatedClient,
    project_id: UUID,
    mission_name: str,
    *,
    metadata: Optional[Dict[str, str]] = None,
    ignore_missing_tags: bool = False,
    required_tags: Optional[List[str]] = None,
) -> UUID:
    """\
    creates a new mission with the given name and project_id

    if check_exists is True, the function will return the existing mission_id,
    otherwise if the mission already exists an error will be raised
    """
    if metadata is None:
        metadata = {}

    _validate_mission_name(client, project_id, mission_name)

    if required_tags and not set(required_tags).issubset(metadata.keys()):
        raise InvalidMissionMetadata(
            f"Mission tags `{required_tags}` are required but missing from metadata: {metadata}"
        )

    # we need to translate tag keys to tag type ids
    tags = _get_tags_map(client, metadata)

    payload = {
        "name": mission_name,
        "projectUUID": str(project_id),
        "tags": {str(k): v for k, v in tags.items()},
        "ignoreTags": ignore_missing_tags,
    }
    resp = client.post(CREATE_MISSION, json=payload)
    resp.raise_for_status()
    _validate_mission_created(client, str(project_id), mission_name)

    return UUID(resp.json()["uuid"], version=4)


def _create_project(
    client: AuthenticatedClient, project_name: str, description: str
) -> UUID:

    _validate_project_name(client, project_name, description)
    payload = {"name": project_name, "description": description}
    resp = client.post(CREATE_PROJECT, json=payload)
    resp.raise_for_status()

    return UUID(resp.json()["uuid"], version=4)


def _validate_project_name(
    client: AuthenticatedClient, project_name: str, description: str
) -> None:
    if not _project_name_is_available(client, project_name):
        raise ProjectExists(f"Project with name: `{project_name}` already exists")

    if project_name.endswith(" "):
        raise ProjectValidationError(
            f"Project name must not end with a tailing whitespace: `{project_name}`"
        )

    if not description:
        raise ProjectValidationError("Project description is required")


def _validate_tag_value(tag_value, tag_datatype) -> None:
    if tag_datatype == "NUMBER":
        try:
            float(tag_value)
        except ValueError:
            raise InvalidMissionMetadata(f"Value '{tag_value}' is not a valid NUMBER")
    elif tag_datatype == "BOOLEAN":
        if tag_value.lower() not in {"true", "false"}:
            raise InvalidMissionMetadata(
                f"Value '{tag_value}' is not a valid BOOLEAN (expected 'true' or 'false')"
            )
    else:
        pass  # any string is fine
    # TODO: add check for LOCATION tag datatype


def _get_metadata_type_id_by_name(
    client: AuthenticatedClient, tag_name: str
) -> Tuple[Optional[UUID], str]:
    resp = client.get(TAG_TYPE_BY_NAME, params={"name": tag_name, "take": 1})

    if resp.status_code in (403, 404):
        return None

    resp.raise_for_status()
    try:
        data = resp.json()["data"][0]
    except IndexError:
        return None, None

    return UUID(data["uuid"], version=4), data["datatype"]


def _get_tags_map(
    client: AuthenticatedClient, metadata: Dict[str, str]
) -> Dict[UUID, str]:
    # TODO: this needs a better endpoint
    # why are we using metadata type ids as keys???
    ret = {}
    for key, val in metadata.items():
        metadata_type_id, tag_datatype = _get_metadata_type_id_by_name(client, key)
        if metadata_type_id is None:
            raise InvalidMissionMetadata(f"metadata field: {key} does not exist")
        _validate_tag_value(val, tag_datatype)
        ret[metadata_type_id] = val
    return ret


def _update_mission(
    client: AuthenticatedClient, mission_id: UUID, *, metadata: Dict[str, str]
) -> None:
    tags_dct = _get_tags_map(client, metadata)
    payload = {
        "missionUUID": str(mission_id),
        "tags": {str(k): v for k, v in tags_dct.items()},
    }
    resp = client.post(UPDATE_MISSION, json=payload)

    if resp.status_code == 404:
        raise MissionNotFound
    if resp.status_code == 403:
        raise AccessDenied(f"cannot update mission: {mission_id}")

    resp.raise_for_status()


def _update_project(
    client: AuthenticatedClient,
    project_id: UUID,
    *,
    description: Optional[str] = None,
    new_name: Optional[str] = None,
) -> None:
    if description is None and new_name is None:
        raise ValueError("either description or new_name must be provided")

    body = {}
    if description is not None:
        body["description"] = description
    if new_name is not None:
        body["name"] = new_name
    resp = client.put(f"{UPDATE_PROJECT}/{project_id}", json=body)
    resp.raise_for_status()


def _get_api_version() -> Tuple[int, int, int]:
    config = get_config()
    client = httpx.Client()

    resp = client.get(
        f"{config.endpoint.api}{GET_STATUS}", headers={CLI_VERSION_HEADER: __version__}
    )
    vers = resp.headers["kleinkram-version"].split(".")

    return tuple(map(int, vers))  # type: ignore


def _claim_admin(client: AuthenticatedClient) -> None:
    """\
    the first user on the system could call this
    """
    response = client.post(CLAIM_ADMIN)
    response.raise_for_status()
    return


FILE_DELETE_MANY = "/files/deleteMultiple"


def _delete_files(
    client: AuthenticatedClient, file_ids: Sequence[UUID], mission_id: UUID
) -> None:
    payload = {
        "uuids": [str(file_id) for file_id in file_ids],
        "missionUUID": str(mission_id),
    }
    resp = client.post(FILE_DELETE_MANY, json=payload)
    resp.raise_for_status()


MISSION_DELETE_ONE = "/missions/{}"


def _delete_mission(client: AuthenticatedClient, mission_id: UUID) -> None:
    resp = client.delete(MISSION_DELETE_ONE.format(mission_id))

    # 409 is returned if the mission has files
    # 403 is returned if the mission does not exist / user cant delete

    resp.raise_for_status()


PROJECT_DELETE_ONE = "/projects/{}"


def _delete_project(client: AuthenticatedClient, project_id: UUID) -> None:
    resp = client.delete(PROJECT_DELETE_ONE.format(project_id))
    resp.raise_for_status()
