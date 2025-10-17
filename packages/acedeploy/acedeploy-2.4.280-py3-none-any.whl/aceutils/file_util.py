import csv
import errno
import json
import logging
import os
import fnmatch
from typing import Dict, List, Union

import jsonschema
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def get_content(file_path: str, encoding: str = "utf-8-sig") -> str:
    """
        Reads and returns the file content of given path, without further modifications.
    Args:
        file_path: absolute file path to a file
        encoding: specific code page name
    Returns:
        File content as string representation
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def load(file_path: str, encoding: str = "utf-8-sig") -> str:
    """
        Reads and returns the file content of given path.
        Encodings tried in following order:
                utf-8-sig - default
                utf-8
                utf-16-le
                utf-16
                cp1252
    Args:
        file_path: absolute file path to a file
        encoding: specific code page name
    Raises:
        EnvironmentError - if file could not been read with stated encodings
    Returns:
        File content as string representation
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
    else:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except:
            try:
                encoding = "utf-8"
                with open(file_path, "r", encoding=encoding) as file:
                    return file.read()
            except:
                try:
                    encoding = "utf-16-le"
                    with open(file_path, "r", encoding=encoding) as file:
                        return file.read()
                except:
                    try:
                        encoding = "utf-16"
                        with open(file_path, "r", encoding=encoding) as file:
                            return file.read()
                    except:
                        try:
                            encoding = "cp1252"
                            with open(file_path, "r", encoding=encoding) as file:
                                return file.read()
                        except:
                            raise EnvironmentError(
                                f"Can not read file {file_path}. Tried utf-8-sig (BOM), utf-8, utf-16, utf-16-le and cp1252."
                            )


def load_json(file_path: str, encoding: str = "utf-8-sig") -> Union[Dict, None]:
    """
        Reads amd returns a given json file. Content must be in valid JSON Schema.
        Valid JSON Schema should not have any trailing commas.
        Encodings tried in following order:
                utf-8-sig - default
                utf-8
                utf-16-le
                utf-16
                cp1252
    Args:
        file_path: absolute file path to a file
        encoding: specific code page name
        raise_error_on_duplicate_keys: option to raise an error on duplicates
    Raises:
        EnvironmentError - if file could not been read with stated encodings
    Returns:
        File content as dictionary.
        If the file path does not exists None will be returned.
    """
    return json.loads(load(file_path, encoding))

    


def validate_json(schema_file: str, data_file: str, schema_path_resolver: str = '') -> bool:
    """
        Validates a JSON file against a given schema file.
    Args:
        schema_file: absolute file path to a JSON schema
        data_file: relative file path to a JSON file
        schema_path_resolver: absolute folder path to the JSON schema - optional and needed for schema references in complex schemas
    Returns:
        boolean: True is sucessful, False if failed
    """
    schema = load_json(schema_file)

    data = load_json(data_file)


    if schema_path_resolver:
        base_uri = 'file:///{0}/'.format(schema_path_resolver)
        resolver = jsonschema.RefResolver(base_uri, schema)

    try:
        if schema_path_resolver:
            jsonschema.validate(data, schema, resolver=resolver)
        else:
            jsonschema.validate(data, schema)
    except jsonschema.ValidationError as err:
        log.error(
            f"FAILED validation JSON [ '{data_file}' ] for SCHEMA [ '{schema_file}' ] \n with ERROR [ '{err.message}' ]"
        )
        return False
    except jsonschema.SchemaError as err:
        log.error(
            f"INVALID json SCHEMA [ '{schema_file}' ] with ERROR [ '{err.message}' ]"
        )
        return False
    return True


def get_path(relative_path: List[str]) -> str:
    """
        Return the absolute path of the given relative (to the module root) path.
    Args:
        relative_path: List[str] - Path relative to module root, given as array, e.g. ['subfolder1', 'subfolder2', 'myfile.sql']
    Returns:
        absoulute path as string
    """
    module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = module_root
    for rp in relative_path:
        path = os.path.join(path, rp)
    return path


def save_json(file_path, dictionary) -> None:
    """
    Save a dictionary as a json file.
    """
    with open(file_path, "w") as f:
        json.dump(dictionary, f, indent=4)


def save_list_of_dicts_as_csv(file_path, list_of_dicts, delimiter=",") -> None:
    """
    Save a list of dictionaries as a csv file.
    All dictionaries must have the same keys.
    """
    if len(list_of_dicts) == 0:
        first_keys = []
    else:
        first_keys = list_of_dicts[0].keys()
    for d in list_of_dicts:
        if d.keys() != first_keys:
            raise ValueError("All dictionaries in the list must have the same keys")
    with open(file_path, "w", encoding="utf8", newline="") as f:
        fc = csv.DictWriter(f, fieldnames=first_keys, delimiter=delimiter)
        fc.writeheader()
        fc.writerows(list_of_dicts)


def get_filelist(path: str, fileextension_filter: List[str] = ()) -> List[str]:
    """
    Return a list of all files in all subdirectories of the given path.
    Optionally filter list to contain only files which match a given list of file extensions (case insensitive.)
    """
    fileextension_filter_lower = tuple([f.lower() for f in fileextension_filter])
    matches = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            if fileextension_filter_lower:
                if not filename.lower().endswith(fileextension_filter_lower):
                    continue
            matches.append(os.path.join(root, filename))
    return matches


def filter_filelist_negative(filenames: List[str], filters: List[str]) -> List[str]:
    """
    Given a list of filenames, apply negatives filters: Remove all matches from the list.
    """
    filtered_filenames = []
    for filename in filenames:
        if not any(fnmatch.fnmatch(filename, pattern) for pattern in filters):
            filtered_filenames.append(filename)
    return filtered_filenames
