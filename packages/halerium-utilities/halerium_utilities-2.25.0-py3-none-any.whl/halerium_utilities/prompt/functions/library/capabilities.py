import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional
from traceback import format_exception_only

from halerium_utilities.prompt.capabilities import (
    get_capability_groups_async,
    get_capability_group_async,
    delete_capability_group_async, 
    create_capability_group_async,
    update_capability_group_async,
    add_function_to_capability_group_async,
    delete_function_from_capability_group_async,
    update_function_in_capability_group_async,
    write_capability_group_to_file_async,
    create_capability_group_from_file_async,
    update_capability_group_from_file_async,
)
from halerium_utilities.prompt.capabilities.capabilities import CapabilityGroupException


BACKUP_FOLDER = Path.home() / ".capability_editor"


async def _backup_capability(capability):
    BACKUP_FOLDER.mkdir(exist_ok=True)

    datestring = datetime.now().isoformat().replace(":", "-")
    name = capability["name"]

    filename = f"{name}-{datestring}.capabilities"

    await write_capability_group_to_file_async(filepath=BACKUP_FOLDER / filename,
                                               capability=capability)

    _cleanup_backups(name)


def _find_backups(name: str = None):
    if not BACKUP_FOLDER.exists():
        return []

    backups = []
    for path in BACKUP_FOLDER.glob("*.capabilities"):
        if (not name) or path.name[:-40] == name:
            try:
                with open(path, "r") as f:
                    capa_group = json.load(f)
                capa_group = capa_group["capabilities"][0]
                _name = capa_group["name"]
                functions = [f["function"] for f in capa_group["functions"]]
                backups.append({
                    "backup_file": str(path.name),
                    "name": _name,
                    "functions": functions,
                })
            except Exception as e:
                backups.append({
                    "backup_file": str(path.name),
                    "error": e
                })

    return sorted(backups, key=lambda el: el["backup_file"])


def _cleanup_backups(name):
    backups = _find_backups(name=name)

    # only keep last 10 iterations
    for backup in backups[:-10]:
        path = BACKUP_FOLDER / backup["backup_file"]
        if path.exists():
            path.unlink()


async def get_all_capability_groups() -> List[Dict]:
    try:
        return await get_capability_groups_async()
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def get_capability_group(name: str) -> Dict:
    try:
        return await get_capability_group_async(name)
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def delete_capability_group(name: str) -> Dict:
    try:
        return await delete_capability_group_async(name)
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def create_capability_group(name: str,
                                  runner_type: Optional[str] = None,
                                  shared_runner: Optional[bool] = None,
                                  setup_commands: Optional[str] = None,
                                  source_code: Optional[str] = None,
                                  functions: Optional[str] = None) -> Dict:
    if setup_commands is not None:
        setup_commands = json.loads(setup_commands)
    if functions is not None:
        functions = json.loads(functions)

    try:
        result = await create_capability_group_async(
            name=name,
            runner_type=runner_type,
            shared_runner=shared_runner,
            setup_commands=setup_commands,
            source_code=source_code,
            functions=functions)
        await _backup_capability(result)
        return result
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def update_capability_group(name: str,
                                  new_name: Optional[str] = None,
                                  runner_type: Optional[str] = None,
                                  shared_runner: Optional[bool] = None,
                                  setup_commands: Optional[str] = None,
                                  source_code: Optional[str] = None,
                                  functions: Optional[str] = None) -> Dict:
    if setup_commands is not None:
        setup_commands = json.loads(setup_commands)
    if functions is not None:
        functions = json.loads(functions)

    try:
        result = await update_capability_group_async(
            name=name, new_name=new_name,
            runner_type=runner_type,
            shared_runner=shared_runner,
            setup_commands=setup_commands,
            source_code=source_code,
            functions=functions)
        await _backup_capability(result)
        return result
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def add_function_to_group(name: str,
                                source_code: Optional[str] = None,
                                function: Optional[str] = None) -> Dict:
    if function is not None:
        function = json.loads(function)
    
    try:
        result = await add_function_to_capability_group_async(name, source_code, function)
        await _backup_capability(result)
        return result
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def delete_function_from_group(name: str, function: str) -> Dict:
    try:
        result = await delete_function_from_capability_group_async(name, function)
        await _backup_capability(result)
        return result
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def update_function_in_group(name: str,
                                   old_function_name: str,
                                   source_code: Optional[str] = None,
                                   new_function: Optional[str] = None) -> Dict:
    if new_function is not None:
        new_function = json.loads(new_function)
    
    try:
        result = await update_function_in_capability_group_async(
            name, 
            old_function_name, 
            source_code, 
            new_function
        )
        await _backup_capability(result)
        return result
    except Exception as exc:
        return "".join(format_exception_only(exc))


async def restore_capability_group(action: Literal["view", "restore"],
                                   name: str = None,
                                   backup_file: str = None):

    if action == "view":
        return _find_backups(name)
    elif action == "restore":
        if not backup_file:
            return "Error: backup_file must be specified for action 'restore'."
        backup_file_path = BACKUP_FOLDER / backup_file
        if not backup_file_path.exists():
            return f"Error: backup_file '{backup_file}' was not found."
        if not name:
            return "Error: name must be specified for action 'restore'."

        use_create = False
        try:
            await get_capability_group_async(name)
        except CapabilityGroupException:
            use_create = True

        try:
            if use_create:
                result = await create_capability_group_from_file_async(
                    name=name,
                    filepath=backup_file_path
                )
            else:
                result = await update_capability_group_from_file_async(
                    name=name,
                    filepath=backup_file_path
                )
            return result
        except Exception as exc:
            return "".join(format_exception_only(exc))
