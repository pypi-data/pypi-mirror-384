import json
import logging
import os
import subprocess
from operator import itemgetter
from typing import Any, Dict, List, Union

from yaml import safe_load


# Get a logger
def _get_logger() -> logging.Logger:
    logging_level = logging.ERROR

    logger = logging.getLogger()
    logger.setLevel(logging_level)
    logging.basicConfig(
        format="%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
        level=logging_level,
    )
    return logger


# Takes care of the path
def sanitise_file_path(file_path: str, working_directory: str = ".") -> str:
    if working_directory == ".":
        return file_path
    elif working_directory.endswith("/"):
        return f"{working_directory}{file_path}"
    else:
        return f"{working_directory}/{file_path}"


# Runs tflocal and return the json manifest
def synthetise_terraform_json(file_path: str, working_directory: str = ".") -> Any:
    os.makedirs("tests/__snapshots__", exist_ok=True)

    # Run tflocal script
    subprocess.run(
        f"{os.environ["TF_TEST_CMD"]} init", shell=True, check=True, cwd=working_directory, env=os.environ.copy()
    )
    subprocess.run(
        f"{os.environ["TF_TEST_CMD"]} validate", shell=True, check=True, cwd=working_directory, env=os.environ.copy()
    )
    subprocess.run(
        f"{os.environ["TF_TEST_CMD"]} plan -out={file_path}.plan",
        shell=True,
        check=True,
        cwd=working_directory,
        env=os.environ.copy(),
    )
    subprocess.run(
        f"{os.environ["TF_TEST_CMD"]} show -json {file_path}.plan > {file_path}.json",
        shell=True,
        check=True,
        cwd=working_directory,
        env=os.environ.copy(),
    )

    # Load the generated json and return
    with open(f"{sanitise_file_path(file_path, working_directory)}.json") as f:
        return json.load(f)


# Sort the lists within the dictionary and sub-dictionaries
def sort_lists_in_dictionary(
    dictionary: Dict[str, Any], sort_key: str = "address", sort_attributes: List[str] = ["modules", "child_modules"]
) -> Dict[str, Any]:
    for k in dictionary.keys():

        # If list, sort and call resursively for each element
        if isinstance(dictionary[k], list) and k in sort_attributes:
            sorted_list = sorted(dictionary[k], key=itemgetter(sort_key))
            dictionary[k] = []
            for element in sorted_list:
                if isinstance(element, dict):
                    element = sort_lists_in_dictionary(
                        dictionary=element, sort_key=sort_key, sort_attributes=sort_attributes
                    )
                dictionary[k].append(element)

        # If dictionary, call recursively
        if isinstance(dictionary[k], dict):
            dictionary[k] = dict(
                sort_lists_in_dictionary(dictionary=dictionary[k], sort_key=sort_key, sort_attributes=sort_attributes)
            )

    return dictionary


# DRY to load json from file
def get_json_from_file(file_path: str, working_directory: str = ".") -> Any:
    payload = {}
    with open(sanitise_file_path(file_path, working_directory)) as f:
        payload = json.load(f)
    return payload


# Verify if the expectaiton contains the right format
def verify_expectation_schema(expectation: Dict[str, Any], file_path: str) -> None:

    # Mandatory fields
    mandatory_fields = {"description", "module", "synthesis", "planned_values"}
    if not mandatory_fields.issubset(expectation.keys()):
        raise ValueError(
            f"Expectation '{file_path}' is missing one or more of the mandatory attributes {mandatory_fields}"
        )

    # Check assertions attribute presence
    for attribute in ["synthesis", "planned_values"]:
        if not {"assertions"}.issubset(expectation[attribute].keys()):
            raise ValueError(f"Expectation '{file_path}' '{attribute}' attribute is missing an 'assertions' attribute")

    return


# Load the expectations into dictionary
def _load_expectations(folder_path: str) -> List[Dict[str, Any]]:
    module_expectations: List[Dict[str, Any]] = []

    # If folder doesn't exist, return
    if not os.path.isdir(folder_path):
        return module_expectations

    # Iterate all files in the folder
    for root, _, files in os.walk(folder_path):
        path = root.split(os.sep)
        for file_name in files:
            # Only process yaml files
            if file_name.split(".")[-1] not in ["yml", "yaml"]:
                continue

            # Safe-load the yaml
            file_path = "/".join(path + [file_name])
            with open(file_path, "r", encoding="utf-8") as f:
                expectations = safe_load(f)

                # Verify if the expecations are correct
                verify_expectation_schema(expectation=expectations, file_path=file_path)
                module_expectations.append(expectations)

    return module_expectations


# Find the objects to iterate within the assertions definition
def _get_expected_objects(
    module: str,
    expectation: Any,
    address_attribute: str,
    stack_hierarchy: List[str],
    tracked_objects: List[Any],
) -> List[Any]:

    # We have a list
    if isinstance(expectation, list):
        for element in expectation:
            tracked_objects = _get_expected_objects(
                module=module,
                expectation=element,
                address_attribute=address_attribute,
                stack_hierarchy=stack_hierarchy,
                tracked_objects=tracked_objects,
            )

    # We have a dictionary / object
    if isinstance(expectation, dict):

        # If the address attribute is there, track the object
        if address_attribute in expectation.keys():
            expectation[address_attribute] = expectation[address_attribute].replace("$MODULE", module)
            tracked_objects.append(
                {
                    "expectation": expectation,
                    "stack_hierarchy": stack_hierarchy,
                }
            )

        # Recursively search the object for the keys
        else:
            for k in expectation.keys():
                tracked_objects = _get_expected_objects(
                    module=module,
                    expectation=expectation[k],
                    address_attribute=address_attribute,
                    stack_hierarchy=stack_hierarchy + [k],
                    tracked_objects=tracked_objects,
                )

    return tracked_objects


# Find the objects within the snapshot by attribute+value+hierarchy
def _get_snapshot_objects(
    snapshot: Any,
    address_attribute: str,
    address_value: str,
    stack_hierarchy: List[str],
    tracked_objects: List[Any],
) -> List[Any]:

    # We have a list
    if isinstance(snapshot, list):
        for element in snapshot:
            tracked_objects = _get_snapshot_objects(
                snapshot=element,
                address_attribute=address_attribute,
                address_value=address_value,
                stack_hierarchy=stack_hierarchy,
                tracked_objects=tracked_objects,
            )

    # We have a dictionary / object
    if isinstance(snapshot, dict):

        # Add object if found
        if snapshot.get(address_attribute, "") == address_value:
            tracked_objects.append(snapshot)

            # Return tracked objects
            return tracked_objects

        # If there is more hierarchy, keep going
        if stack_hierarchy:
            next_hierarchy = stack_hierarchy.pop(0)
            tracked_objects = _get_snapshot_objects(
                snapshot=snapshot[next_hierarchy],
                address_attribute=address_attribute,
                address_value=address_value,
                stack_hierarchy=stack_hierarchy,
                tracked_objects=tracked_objects,
            )

    return tracked_objects


# Let's assert our expectation
def _assert_snapshot_matches_expectation(
    snapshot: Any,
    expectation: Any,
    module: str,
    address_attribute: str,
    stack_hierarchy: List[str],
    logger: Union[logging.Logger, None] = None,
) -> bool:
    found = False

    # List
    if isinstance(expectation, list):
        # Check type symmetry
        assert isinstance(snapshot, list)
        for e in expectation:
            for s in snapshot:
                found = found or _assert_snapshot_matches_expectation(
                    snapshot=s,
                    expectation=e,
                    module=module,
                    address_attribute=address_attribute,
                    stack_hierarchy=stack_hierarchy,
                    logger=logger,
                )
                if not found:
                    return False

    # Dictionary
    elif isinstance(expectation, dict):
        # Check type symmetry
        assert isinstance(snapshot, dict)

        # Check what's inside
        for k in expectation.keys():

            # Inject recursion metadata to help locate the assertion error
            stack_sub_hierarchy = list(stack_hierarchy)
            if "address" in expectation.keys():
                stack_sub_hierarchy.append(f"resource({expectation["address"]})")
            stack_sub_hierarchy.append(k)

            # Keep searchig for assertions
            found = _assert_snapshot_matches_expectation(
                snapshot=snapshot[k],
                expectation=expectation[k],
                module=module,
                address_attribute=address_attribute,
                stack_hierarchy=stack_sub_hierarchy,
                logger=logger,
            )
            if not found:
                return False

    # Scalar
    else:
        # Check the types - dict (i.e. wrong types)
        if isinstance(snapshot, dict):
            return False

        # Check the types - list (i.e. scalar in list?)
        elif isinstance(snapshot, list):
            return expectation in snapshot

        else:
            # Both are scalars
            # Ensure it's not null marker
            if expectation == "$NOTNULL" and snapshot:
                found = True
            else:
                if expectation:
                    if expectation.replace("$MODULE", module) == snapshot:
                        found = True
                    else:
                        msg = f"Module: '{module}' expected '{expectation}' but got '{snapshot}' in {".".join(stack_hierarchy)}"
                        if logger:
                            logger.error(msg)
                        return False
                else:
                    found = True

    return found


# Run the assertions
def _run_assertions(
    snapshot: Dict[str, Any],
    expectations: List[Any],
    snapshot_type: str,
    logger: Union[logging.Logger, None] = None,
) -> None:

    # Verify input
    valid_snapshot_types = ["synthesis", "planned_values"]
    if snapshot_type not in valid_snapshot_types:
        raise ValueError(f"Argument 'snapshot_type' must be one of '{json.dumps(valid_snapshot_types)}'")

    # Let's go through the imported assertions
    for expectation in expectations:
        module = expectation["module"]
        assertions = expectation[snapshot_type].get("assertions", {})

        # Skip if there are no assertions to test
        if not assertions:
            continue

        # Isolate the relevant part of the snapshot
        snapshot_to_compare = {}

        # If the snapshot we are validating is for the synthesis
        if snapshot_type == "synthesis":
            snapshot_to_compare = snapshot.get("module_calls", {}).get(module.replace("module.", ""), {})

        # If the snapshot we are validating is for planned
        if snapshot_type == "planned_values":
            for child_module in snapshot.get("root_module", {}).get("child_modules", []):
                if child_module["address"] == module:
                    snapshot_to_compare = child_module
                    break

        # Get the success criteria to test from the expectations
        assertions_criteria = _get_expected_objects(
            module=module,
            expectation=assertions,
            address_attribute="address",
            stack_hierarchy=[],
            tracked_objects=[],
        )

        # Search the snapshot for the presence of the success criteria
        for assertion_criterion in assertions_criteria:
            tracked_objects = _get_snapshot_objects(
                snapshot=snapshot_to_compare,
                address_attribute="address",
                address_value=assertion_criterion["expectation"]["address"],
                stack_hierarchy=list(assertion_criterion["stack_hierarchy"]),
                tracked_objects=[],
            )

            # Ensure we found eactly one object
            assert len(tracked_objects) == 1

            # Ensure the found object matches the expectation
            assert _assert_snapshot_matches_expectation(
                snapshot=tracked_objects[0],
                expectation=assertion_criterion["expectation"],
                module=module,
                address_attribute="address",
                stack_hierarchy=[],
                logger=logger,
            )

    return


# User method
def assert_expectations(
    snapshot: Dict[str, Any], snapshot_type: str, folder_path: str = "expectations", working_directory: str = "."
) -> None:

    # Load expectations
    expectations = _load_expectations(folder_path=f"{working_directory}/{folder_path}")

    # If no expectations found, return
    if not expectations:
        return

    # Test expectations
    _run_assertions(
        snapshot=snapshot,
        expectations=expectations,
        snapshot_type=snapshot_type,
        logger=_get_logger(),
    )

    return
