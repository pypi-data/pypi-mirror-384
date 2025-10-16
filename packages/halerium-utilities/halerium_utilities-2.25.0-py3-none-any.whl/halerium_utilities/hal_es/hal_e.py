import asyncio
import httpx
import os
import time

from typing import List, Literal, Optional

from halerium_utilities.board import Board
from halerium_utilities.hal_es.schemas import HalEData, HalEPayload
from halerium_utilities.utils.workspace_paths import runner_path_to_workspace_path


def _get_endpoint():
    tenant = os.getenv('HALERIUM_TENANT_KEY', '')
    workspace = os.getenv('HALERIUM_PROJECT_ID', '')
    base_url = os.getenv('HALERIUM_BASE_URL', '')

    return f"{base_url}/api/tenants/{tenant}/projects/{workspace}/runners/{os.environ['HALERIUM_ID']}/token-access/hal-es"


def get_workspace_hales() -> List["HalE"]:
    """
    Fetches HalE instances for the workspace and converts the data into HalE objects.

    Returns
    -------
    List[HalE]
        A list of HalE instances representing available boards in the workspace.
    """
    raw_data = _get_workspace_hale_data()
    hales = []

    for hale_data in raw_data.get('data', []):
        hale_instance = _create_hale_from_data(hale_data)
        if hale_instance:
            hales.append(hale_instance)
        else:
            print(f"Failed to create HalE instance for: {hale_data}")

    return hales


async def get_workspace_hales_async() -> List["HalE"]:
    """
    Fetches available HalE instances in the workspace asynchronously.

    Returns
    -------
    List[HalE]
        A list of HalE instances representing available HalE boards in the workspace.
    """
    raw_data = await _get_workspace_hale_data_async()
    hales = []

    for hale_data in raw_data.get('data', []):
        hale_instance = _create_hale_from_data(hale_data)
        if hale_instance:
            hales.append(hale_instance)
        else:
            print(f"Failed to create HalE instance for: {hale_data}")

    return hales


def _get_workspace_hale_data() -> List[dict]:
    """
    Fetches raw data of available HalEs in the workspace.

    Returns
    -------
    List[dict]
        A list of dictionaries representing available HalE boards in the workspace.
    """
    endpoint = _get_endpoint()
    with httpx.Client() as client:
        response = client.get(
            endpoint,
            headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]}
        )
        response.raise_for_status()
        return response.json()


async def _get_workspace_hale_data_async() -> List[dict]:
    """
    Fetches raw data of available HalEs in the workspace asynchronously.

    Returns
    -------
    List[dict]
        A list of dictionaries representing available HalE boards in the workspace.
    """
    endpoint = _get_endpoint()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            endpoint,
            headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]}
        )
        response.raise_for_status()
        return response.json()


def _get_hale_data_by_name(hale_name: str):
    hale_datas = _get_workspace_hale_data()
    for hale_data in hale_datas.get("data", []):
        if hale_data.get("appConfig", {}).get("name") == hale_name:
            return hale_data
    raise ValueError(f"Could not find a Hal-E named '{hale_name}'.")


async def _get_hale_data_by_name_async(hale_name: str):
    hale_datas = await _get_workspace_hale_data_async()
    for hale_data in hale_datas.get("data", []):
        if hale_data.get("appConfig", {}).get("name") == hale_name:
            return hale_data
    raise ValueError(f"Could not find a Hal-E named '{hale_name}'.")


def _is_hale_name_occupied(hale_name):
    try:
        _get_hale_data_by_name(hale_name)
        return True
    except ValueError:
        return False


async def _is_hale_name_occupied_async(hale_name):
    try:
        await _get_hale_data_by_name_async(hale_name)
        return True
    except ValueError:
        return False


def _get_temp_boardfile():
    # save board to temp file
    basename = ".board_template"
    fname = basename + ".board"
    counter = 0
    while os.path.exists(fname):
        counter += 1
        fname = basename + f"_{counter}.board"
    return fname


def _cleanup_temp_boardfile(fname):
    if os.path.exists(fname):
        os.unlink(fname)


def _create_workspace_hale_prep(
        fname: str,
        name: str,
        description: str = None,
        board: Board = None,
        access: Literal["workspace", "company-user-groups", "company", "public"] = None,
        log_sessions: bool = True,
        log_path: str = None
):
    if board:
        board = Board(board)
    else:
        board = Board()
    log_sessions = bool(log_sessions)
    if log_sessions:
        if log_path:
            workspace_log_path = runner_path_to_workspace_path(log_path)
        else:
            workspace_log_path = f"/{name}"
    else:
        workspace_log_path = None
    if not access:
        access = "workspace"
    description = str(description) if description else ""

    board.to_json(fname)

    template_board_workspace_path = runner_path_to_workspace_path(fname)
    payload = HalEPayload.validate({
        "appConfig": {
            "appType": "hal-e",
            "name": name,
            "description": description,
            "accessType": access,
            "appParams": {
                "sourcePath": template_board_workspace_path,
                "config": {
                    "sessions": {
                        "path": workspace_log_path,
                        "persistSession": log_sessions
                    }
                }
            }
        }
    })
    return payload


def create_workspace_hale(
        name: str,
        description: str = "",
        board: Board = None,
        access: Literal["workspace", "company-user-groups", "company", "public"] = "workspace",
        log_sessions: bool = True,
        log_path: str = None,
) -> "HalE":
    if _is_hale_name_occupied(name):
        raise ValueError(f"Hal-E name {name} is already taken.")

    fname = _get_temp_boardfile()
    try:
        payload = _create_workspace_hale_prep(
            fname=fname, name=name, description=description, board=board,
            access=access, log_sessions=log_sessions, log_path=log_path)

        time.sleep(1)  # wait 1 second to allow the file to propagate through efs

        endpoint = _get_endpoint()
        with httpx.Client() as client:
            response = client.post(
                endpoint,
                headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]},
                json=payload.dict()
            )
            response.raise_for_status()
            hale_data = response.json()["data"]
        return _create_hale_from_data(hale_data)
    finally:
        _cleanup_temp_boardfile(fname)


async def create_workspace_hale_async(
        name: str,
        description: str = "",
        board: Board = None,
        access: Literal["workspace", "company-user-groups", "company", "public"] = "workspace",
        log_sessions: bool = True,
        log_path: str = None,
) -> "HalE":
    if await _is_hale_name_occupied_async(name):
        raise ValueError(f"Hal-E name {name} is already taken.")

    fname = _get_temp_boardfile()
    try:
        payload = _create_workspace_hale_prep(
            fname=fname, name=name, description=description, board=board,
            access=access, log_sessions=log_sessions, log_path=log_path)

        await asyncio.sleep(1)  # wait 1 second to allow the file to propagate through efs

        endpoint = _get_endpoint()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]},
                json=payload.dict()
            )
            response.raise_for_status()
            hale_data = response.json()["data"]
        return _create_hale_from_data(hale_data)
    finally:
        _cleanup_temp_boardfile(fname)


def _create_hale_from_data(hale_data: dict) -> Optional["HalE"]:
    """
    Creates a HalE instance from a hale_data.

    Parameters
    ----------
    hale_data : dict
        A dictionary containing the necessary keys to instantiate a HalE object.

    Returns
    -------
    HalE
        A HalE instance
    """
    hale_data_model = HalEData.validate(hale_data)
    return HalE(hale_data_model)


class HalE:
    """
    Represents a HalE instance within a workspace.
    """

    def __init__(self, hale_data: HalEData):
        """
        Initializes a HalE instance with the provided details.

        Parameters
        ----------
        hale_data : HalEData or dict
        """
        self.name = None
        self.description = None
        self.access = None
        self.log_sessions = None
        self.log_path = None

        self.init_url = None
        self.template_board = None

        self._set_params(hale_data)

    def _set_params(self, hale_data):
        hale_data = HalEData.validate(hale_data)
        app_config = hale_data.appConfig

        self.name = app_config.name
        self.description = app_config.description
        self.access = app_config.accessType
        self.log_sessions = app_config.appParams.config.sessions.persistSession
        self.log_path = app_config.appParams.config.sessions.path

        self.init_url = hale_data.friendlyUrl
        self.template_board = app_config.appParams.sourcePath

    def _del_params(self):
        self.name = None
        self.description = None
        self.access = None
        self.log_sessions = None
        self.log_path = None

        self.init_url = None
        self.template_board = None

    @property
    def data(self):
        return dict(
            name=self.name,
            description=self.description,
            access=self.access,
            log_sessions=self.log_sessions,
            log_path=self.log_path,
            init_url=self.init_url,
            template_board=self.template_board
        )

    @classmethod
    def from_name(cls, hale_name: str) -> "HalE":
        hale_data = _get_hale_data_by_name(hale_name)
        return _create_hale_from_data(hale_data)

    def get_instance(self) -> Optional["HalESession"]:
        """
        Creates and returns a new HalESession instance for this HalE.

        Returns
        -------
        Optional[HalESession]
            Returns a HalESession instance if successful, or None if there is an issue.
        """
        from halerium_utilities.hal_es import HalESession

        return HalESession(self)

    def __repr__(self):
        return (f"HalE(name='{self.name}', access='{self.access}', "
                f"template_board='{self.template_board}', init_url='{self.init_url}')")

    def _get_update_endpoint(self):
        endpoint = _get_endpoint()
        endpoint = endpoint.rstrip("/") + f"/{self.name}"
        return endpoint

    def _prepare_update_payload(self,
                                hale_data: dict,
                                name: str = None,
                                description: str = None,
                                access: Literal["workspace", "company-user-groups", "company", "public"] = None,
                                log_sessions: bool = None,
                                log_path: str = None):

        payload = HalEPayload.validate(hale_data)
        if name:
            payload.appConfig.name = name
        if description:
            payload.appConfig.description = description
        if access:
            payload.appConfig.accessType = access

        if log_sessions is not None:
            if log_sessions:
                if not (payload.appConfig.appParams.config.sessions.path or log_path):
                    raise ValueError("'log_sessions' cannot be set to True without providing a log_path.")
            payload.appConfig.appParams.config.sessions.persistSession = bool(log_sessions)

        if log_path:
            workspace_log_path = runner_path_to_workspace_path(log_path)
            payload.appConfig.appParams.config.sessions.path = workspace_log_path

        return HalEPayload.validate(payload.dict())

    def update(self,
               name: str = None,
               description: str = None,
               access: Literal["workspace", "company-user-groups", "company", "public"] = None,
               log_sessions: bool = None,
               log_path: str = None):
        """
        Updates the given properties of the Hal-E.

        Parameters
        ----------
        name : str, optional
        description : str, optional
        access : "workspace", "company-user-groups", "company", or "public", optional
        log_sessions : bool, optional
        log_path : str, optional
        """
        hale_data = _get_hale_data_by_name(self.name)
        if name:
            if _is_hale_name_occupied(name):
                raise ValueError(f"Hal-E name {name} is already taken.")

        endpoint = self._get_update_endpoint()
        payload = self._prepare_update_payload(
            hale_data=hale_data,
            name=name, description=description, access=access,
            log_sessions=log_sessions, log_path=log_path
        )

        with httpx.Client() as client:
            response = client.put(
                endpoint,
                headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]},
                json=payload.dict()
            )
            response.raise_for_status()
            updated_data = response.json()["data"]

        self.__init__(updated_data)

    async def update_async(
            self,
            name: str = None,
            description: str = None,
            access: Literal["workspace", "company-user-groups", "company", "public"] = None,
            log_sessions: bool = None,
            log_path: str = None):
        """
        Updates the given properties of the Hal-E asynchronously.

        Parameters
        ----------
        name : str, optional
        description : str, optional
        access : "workspace", "company-user-groups", "company", or "public", optional
        log_sessions : bool, optional
        log_path : str, optional
        """
        hale_data = await _get_hale_data_by_name_async(self.name)
        if name:
            if await _is_hale_name_occupied_async(name):
                raise ValueError(f"Hal-E name {name} is already taken.")

        endpoint = self._get_update_endpoint()
        payload = self._prepare_update_payload(
            hale_data=hale_data,
            name=name, description=description, access=access,
            log_sessions=log_sessions, log_path=log_path
        )

        async with httpx.AsyncClient() as client:
            response = await client.put(
                endpoint,
                headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]},
                json=payload.dict()
            )
            response.raise_for_status()
            updated_data = response.json()["data"]

        self.__init__(updated_data)

    def delete(self):
        """
        Deletes the Hal-E.
        """
        endpoint = self._get_update_endpoint()
        with httpx.Client() as client:
            response = client.delete(
                endpoint,
                headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]},
            )
            response.raise_for_status()

        self._del_params()

    async def delete_async(self):
        """
        Deletes the Hal-E asynchronously.
        """
        endpoint = self._get_update_endpoint()
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                endpoint,
                headers={"Content-Type": "application/json", "halerium-runner-token": os.environ["HALERIUM_TOKEN"]},
            )
            response.raise_for_status()

        self._del_params()