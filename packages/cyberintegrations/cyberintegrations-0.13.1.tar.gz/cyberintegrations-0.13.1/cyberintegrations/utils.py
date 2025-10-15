# -*- encoding: utf-8 -*-
"""
Copyright (c) 2025

This module contains utils.

"""

import json
import os
from datetime import datetime
from typing import Any, Union, List, Dict

try:
    # WARNING: Used only for classes - ConfigParser, FileHandler
    import pyaml
except Exception:
    pass
from enum import Enum

from .const import CollectionConsts
from .exception import (
    EmptyCredsError,
    InputException,
)


class Validator(object):
    @classmethod
    def validate_collection_name(cls, collection_name, method=None):
        if (
            method == "update"
            and collection_name in CollectionConsts.ONLY_SEARCH_COLLECTIONS
        ):
            raise InputException(
                f"{collection_name} collection must be used only with a search generator."
            )

        collection_names = CollectionConsts.TI_COLLECTIONS_INFO.keys()
        drp_collection_names = CollectionConsts.DRP_COLLECTIONS_INFO.keys()
        if (collection_name not in collection_names) and (
            collection_name not in drp_collection_names
        ):
            raise InputException(
                f"Invalid collection name {collection_name}, "
                f"should be one of this {', '.join(collection_names)} "
                f"or one of this {', '.join(drp_collection_names)}"
            )

    @classmethod
    def validate_date_format(cls, date, formats):
        for i in formats:
            try:
                datetime.strptime(date, i)
                return
            except (TypeError, ValueError):
                pass
        raise InputException(
            f"Invalid date {date}, please use one of this formats: {', '.join(formats)}."
        )

    @classmethod
    def validate_set_iocs_keys_input(cls, keys):
        if not isinstance(keys, dict):
            raise InputException("Keys should be stored in a dict")
        for i in keys.values():
            if not isinstance(i, str):
                raise InputException("Every search path should be a string")

    @classmethod
    def validate_set_keys_input(cls, keys):
        if isinstance(keys, dict):
            for i in keys.values():
                cls.validate_set_keys_input(i)
        elif not isinstance(keys, str):
            raise InputException(
                "Keys should be stored in nested dicts and on the lower level it should be a string."
            )

    @classmethod
    def validate_group_collections(cls, collections):
        if collections in CollectionConsts.GROUP_COLLECTIONS:
            return True

    @classmethod
    def validate_collections_from_yaml(cls, config):
        # WARNING: Need for MISP adapter
        ## type: (dict) -> Literal[True]
        __collections = config.get("collections", None)

        if not __collections:
            raise KeyError("A key 'collections' was not found in YAML file")

        for collection in __collections.keys():
            try:
                __collections[collection]["default_date"] or __collections[
                    collection
                ]["enable"]
            except KeyError as err:
                raise KeyError(
                    "A key {} was not found in 'collection' dict".format(err)
                )

        return True

    @classmethod
    def validate_keys_from_yaml(cls, config):
        # WARNING: Need for MISP adapter
        ## type: (dict) -> Literal[True]
        __collections = config.keys()

        for collection in __collections:
            if not config[collection]:
                raise KeyError(
                    "Keys was not found in collection {}".format(collection)
                )

            for key in config[collection]:
                if not config[collection][key]:
                    raise ValueError("A key '{}' value is empty.".format(key))

        return True


class ParserHelper(object):
    @classmethod
    def find_by_template(cls, feed, keys, **kwargs):
        # type: (dict, dict, Any) -> dict
        parsed_dict = {}
        for key, value in keys.items():
            if isinstance(value, str):
                if value.startswith("*"):
                    parsed_dict.update({key: value[1:]})
                elif value.startswith("#"):  # expect value = "#hash[0]"
                    v, num = value[1:-1].split("[")
                    new_val = cls.find_element_by_key(obj=feed, key=v)
                    if isinstance(new_val, list) and len(new_val) > int(num):
                        parsed_dict.update({key: new_val[int(num)]})
                    else:
                        parsed_dict.update({key: None})
                else:
                    parsed_dict.update(
                        {key: cls.find_element_by_key(obj=feed, key=value)}
                    )
            elif isinstance(value, dict):
                # __nested_dot_path_to_list is used to process lists in the feed.
                # The value in this key is the path to the list in the feed to be expanded.
                # The same pattern (value) is applied to each list item, which allows you to
                # to automatically handle arrays of nested objects.
                if value.get("__nested_dot_path_to_list"):
                    list_obj = cls.find_element_by_key(
                        obj=feed, key=value.get("__nested_dot_path_to_list")
                    )
                    value.pop("__nested_dot_path_to_list", None)
                    if isinstance(list_obj, list):
                        parsed_dict.update(
                            {
                                key: [
                                    cls.find_by_template(nested_feed, value, **kwargs)
                                    for nested_feed in list_obj
                                ]
                            }
                        )
                elif value.get("__concatenate"):
                    concat_values = value.get("__concatenate", {})
                    parsed_dict.update(
                        {
                            key: str(concat_values.get("static"))
                            + str(
                                cls.find_element_by_key(
                                    obj=feed, key=concat_values.get("dynamic")
                                )
                            )
                        }
                    )
                else:
                    parsed_dict.update(
                        {key: cls.find_by_template(feed, value, **kwargs)}
                    )

        return parsed_dict

    @classmethod
    def find_element_by_key(cls, obj, key):
        """
        Recursively finds element or elements in dict.
        """
        path = key.split(".", 1)
        if len(path) == 1:
            if isinstance(obj, list):
                return [i.get(path[0]) for i in obj]
            elif isinstance(obj, dict):
                return obj.get(path[0])
            else:
                return obj
        else:
            if isinstance(obj, list):
                return [
                    cls.find_element_by_key(i.get(path[0]), path[1])
                    for i in obj
                ]
            elif isinstance(obj, dict):
                return cls.find_element_by_key(obj.get(path[0]), path[1])
            else:
                return obj

    @classmethod
    def unpack_iocs(cls, ioc):
        """
        Recursively unpacks all IOCs in one list.
        """
        unpacked = []
        if isinstance(ioc, list):
            for i in ioc:
                unpacked.extend(cls.unpack_iocs(i))
        else:
            if ioc not in ["255.255.255.255", "0.0.0.0", "", None]:
                unpacked.append(ioc)

        return list(set(unpacked))

    @classmethod
    def set_element_by_key(cls, obj, path, value):
        """
        Recursively goes through dicts (and only dicts) and set the key in the end to desired value
        """
        keys = path.split(".", 1)
        if len(keys) == 1:
            obj[keys[0]] = value
            return obj
        else:
            obj[keys[0]] = cls.set_element_by_key(
                obj.get(keys[0]), keys[1], value
            )
            return obj


class AlternativeParserHelper(object):
    @classmethod
    def find_by_template(cls, feed, keys, **kwargs):
        # type: (dict, dict, dict) -> dict
        parsed_dict = {}
        for key, value in keys.items():
            # example -> {"platform": "malwareList.platform"}
            # if value dot-string or a dict ("pls": {"pl1": "malwareList.platform"})
            if isinstance(value, str):
                # avoid adding __nested_dot_path_to_list key in the parsed_dict
                if key != "__nested_dot_path_to_list":
                    if value.startswith("*"):
                        # if we have * ("__description": "*Description string")
                        # replace ("*Description string" -> "Description string")
                        parsed_dict.update({key: value[1:]})
                    elif value.startswith("#"):
                        # if we have # (expect value = "#hash[0]")
                        # retrieve "hash" and "0" from "#hash[0]"
                        v, num = value[1:-1].split("[")
                        # we expect list of items
                        # if we found list and list has items
                        # we take list[0] or list[1] ...
                        new_val = cls.find_element_by_key(obj=feed, key=v)
                        if isinstance(new_val, list) and len(new_val) > int(num):
                            parsed_dict.update({key: new_val[int(num)]})
                        else:
                            # else we put None
                            parsed_dict.update({key: None})
                    else:
                        # no "*", "#" -> find element
                        element = cls.find_element_by_key(obj=feed, key=value)
                        # custom: -convert list to string with elements sep=,
                        if kwargs.get("use_join_to_end_list") and isinstance(element, list):
                            if kwargs.get("except_keys") and key in kwargs.get("except_keys"):
                                parsed_dict.update({key: element})
                            else:
                                parsed_dict.update({key: ",".join(element)})
                        else:
                            parsed_dict.update({key: element})
            elif isinstance(value, dict):
                # if dict -> we go deeper
                # some custom features:
                # - create list of dicts
                if value.get("__nested_dot_path_to_list"):
                    # warning! if [[],[],[]] like indicators[].params[] we rely on JSON?
                    # list_obj -> found object by __nested_dot_path_to_list in feed (should be list)
                    list_obj = cls.find_element_by_key(obj=feed, key=value.get("__nested_dot_path_to_list"))
                    if isinstance(list_obj, list):
                        # apply mapping to each element in list_obj
                        parsed_dict.update({
                            key: [cls.find_by_template(nested_feed, value, **kwargs) for nested_feed in list_obj]
                        })
                    elif isinstance(list_obj, dict):
                        # act in normal way but return list
                        parsed_dict.update({
                            key: [cls.find_by_template(list_obj, value, **kwargs)]
                        })
                # - concatenate static string and found dynamic element
                # key = portal_link, value = {_concatenate}
                elif value.get("__concatenate"):
                    _concat_values = value.get("__concatenate", {})
                    _description = _concat_values.get("__", "")
                    static = _concat_values.get("static")
                    dynamic = cls.find_element_by_key(obj=feed, key=_concat_values.get("dynamic"))
                    if dynamic:
                        _slashed = "/".join(dynamic.split("."))
                        concatenate_result = str(static) + str(_slashed)
                        parsed_dict.update({
                            key: {
                                "__": _description,
                                "static": static,
                                "dynamic": dynamic,
                                "result": concatenate_result
                            }
                        })
                    else:
                        parsed_dict.update({
                            key: {}
                        })

                # act in normal way
                else:
                    parsed_dict.update({key: cls.find_by_template(feed, value, **kwargs)})

        return parsed_dict

    @classmethod
    def find_element_by_key(cls, obj, key):
        """
        Recursively finds element or elements in dict.
        """
        # "malwareList.platform.win" -> ["malwareList", "platform.win"]; "platform.win" -> ["platform", "win"]; "win" ->
        path = key.split(".", 1)
        # if it is a last word in dot-notation string -> act normal
        if len(path) == 1:
            if isinstance(obj, list):
                # extract value in each element of list obj
                return [i.get(path[0]) for i in obj]
            elif isinstance(obj, dict):
                # extract value in dict obj
                return obj.get(path[0])
            else:
                return obj
        # else go deeper in dot-notation string
        else:
            if isinstance(obj, list):
                # extract (data by key, take next key from dot-string) for each element in list
                return [cls.find_element_by_key(i.get(path[0]), path[1]) for i in obj]
            elif isinstance(obj, dict):
                # extract (data by key, take next key from dot-string)
                return cls.find_element_by_key(obj.get(path[0]), path[1])
            else:
                # finnish extraction
                return obj

    @classmethod
    def unpack_iocs(cls, ioc):
        # type: (Union[list, str]) -> list
        """
        Recursively unpacks all IOCs in one list.
        """
        unpacked = []
        if isinstance(ioc, list):
            for i in ioc:
                unpacked.extend(cls.unpack_iocs(i))
        else:
            if ioc not in ['255.255.255.255', '0.0.0.0', '', None]:
                unpacked.append(ioc)

        return list(set(unpacked))


class ConfigParser:
    # WARNING: Need for MISP adapter
    def get_creds(self, config, key="creds"):
        # type: (dict, Union[int, str]) -> Enum
        """Collect credentials from **YAML config**, filtered by **key**"""

        __creds = config.get(key, None)
        if __creds:
            return self.__get_enum_creds(**__creds)
        raise EmptyCredsError("Credentials not found")

    @staticmethod
    def __get_enum_creds(**kwargs):
        """
        Receive any kwargs to return Enum class with them.

        class Creds(Enum):
            API_KEY = kwargs.get("api_key", None)
            API_URL = kwargs.get("api_url", None)

            USERNAME = kwargs.get("username", None)
            PASSWORD = kwargs.get("password", None)

            IP = kwargs.get("ip", None)
            PORT = kwargs.get("port", None)

            BIG_DATA_LIMIT = kwargs.get("big_data_limit", None)
            DEFULT_LIMIT = kwargs.get("default_limit", None)

            DATA_DIR = kwargs.get("data_dir", None)
        """
        return Enum(
            "Creds",
            list(
                zip(
                    # make each key uppercase by 'map' function, which apply 'upper' method to keys
                    list(map(lambda x: x.upper(), kwargs.keys())),
                    kwargs.values(),
                )
            ),
            module=__name__,
        )

    @staticmethod
    def get_collection_default_date(config, collection):
        # type: (dict, str) -> str
        """Check **YAML config** by **collection** key and gather *default_date* field as str"""
        return str(config["collections"][collection]["default_date"])

    @staticmethod
    def get_collection_seq_update(config, collection):
        # type: (dict, dict) -> int
        """Check **YAML config** by **collection** key and gather *seqUpdate* field as int"""
        return int(config["collections"][collection]["default_date"])

    @staticmethod
    def get_enabled_collections(config):
        # type: (dict) -> List[str]
        """Check **YAML config** by *collection* key and gather enabled endpoints in list"""
        __collections = list()
        for collection in config["collections"].keys():
            if config["collections"][collection]["enable"]:
                __collections.append(collection)
        return __collections

    @staticmethod
    def get_disabled_collections(config):
        # type: (dict) -> List[str]
        """Check **YAML config** by *collection* key and gather enabled endpoints in list"""
        __collections = list()
        for collection in config["collections"].keys():
            if not config["collections"][collection]["enable"]:
                __collections.append(collection)
        return __collections


class FileHandler:
    # WARNING: Need for MISP adapter
    """Singleton decorator for borg state logic"""
    # singleton state sharing
    _shared_borg_state = {}

    def __new__(cls, *args, **kwargs):
        obj = super(FileHandler, cls).__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared_borg_state
        return obj

    def __init__(self):
        # self._magic = Magic(mime=True)  # For MIME types
        pass

    @staticmethod
    def is_exist(file):
        # type: (str) -> bool
        """Check if the **file** is exist"""
        return os.path.exists(file)

    @staticmethod
    def is_empty(file):
        # type: (str) -> bool
        """Check if the **file** is empty"""
        return True if os.stat(file).st_size == 0 else False

    def save_collection_info(
        self, config, collection, source="Adapter", **kwargs
    ):
        # type: (str, Union[str, List], str, Dict) -> None
        """
        Update collection metadata at YAML config.

        :param config: path to the config
        :param collection: list of collections or single name
        :param source: **Adapter** for enabled collections only, else for all
        :param kwargs: args like {"seqUpdate": seq_update, "default_date": date}
        """

        if not self.is_exist(config):
            raise FileExistsError("File not exist!")

        # singleton logic
        in_progress = self._shared_borg_state.get("in_progress", False)
        if in_progress:
            while self._shared_borg_state.get("in_progress", False):
                pass
            self._in_progress = True

        # save data logic
        with open(config, "r") as f:
            data = pyaml.yaml.safe_load(f)

        if isinstance(collection, list):
            for col in collection:
                if source == "Adapter":
                    if data["collections"][col]["enable"]:
                        for k, v in kwargs[col].items():
                            data["collections"][col][k] = v
                else:
                    for k, v in kwargs[col].items():
                        data["collections"][col][k] = v
        else:
            if source == "Adapter":
                if data["collections"][collection]["enable"]:
                    for k, v in kwargs.items():
                        data["collections"][collection][k] = v
            else:
                for k, v in kwargs.items():
                    data["collections"][collection][k] = v

        with open(config, "w") as f:
            pyaml.yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        # change status for next instance
        self._in_progress = False

    def read_yaml_config(self, config):
        # type: (str) -> Dict[str, dict]
        """Read **YAML config** data"""
        if not self.is_exist(config):
            raise FileExistsError("File not exist!")
        # if not self.is_yaml(config):
        #     raise FileTypeError("File type not supported! Expected YML file!")

        # singleton logic
        in_progress = self._shared_borg_state.get("in_progress", False)
        if in_progress:
            while self._shared_borg_state.get("in_progress", False):
                pass
            self._in_progress = True

        with open(config, "r") as f:
            _config = pyaml.yaml.safe_load(f)

        # change status for next instance
        self._in_progress = False

        return _config

    def read_json_config(self, config):
        # type: (str) -> Dict[str, dict]
        """Read **JSON config** data"""
        if not self.is_exist(config):
            raise FileExistsError("File not exist!")
        # if not self.is_json(config):
        #     raise FileTypeError("File type not supported! Expected JSON file!")

        # singleton logic
        in_progress = self._shared_borg_state.get("in_progress", False)
        if in_progress:
            while self._shared_borg_state.get("in_progress", False):
                pass
            self._in_progress = True

        with open(config, "r") as f:
            _config = json.load(f)

        # change status for next instance
        self._in_progress = False

        return _config

    def save_data_to_yaml_config(self, data, config):
        # type: (Any, str) -> None
        """Save **YAML config** data"""
        if not self.is_exist(config):
            raise FileExistsError("File not exist!")
        # if not self.is_yaml(config):
        #     raise FileTypeError("File type not supported! Expected YML file!")

        # singleton logic
        in_progress = self._shared_borg_state.get("in_progress", False)
        if in_progress:
            while self._shared_borg_state.get("in_progress", False):
                pass
            self._in_progress = True

        with open(config, "w") as f:
            pyaml.yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        # change status for next instance
        self._in_progress = False

    def save_data_to_json_config(self, data, config):
        # type: (Any, str) -> None
        """Save **JSON config** data"""
        if not self.is_exist(config):
            raise FileExistsError("File not exist!")
        # if not self.is_json(config):
        #     raise FileTypeError("File type not supported! Expected JSON file!")

        # singleton logic
        in_progress = self._shared_borg_state.get("in_progress", False)
        if in_progress:
            while self._shared_borg_state.get("in_progress", False):
                pass
            self._in_progress = True

        with open(config, "w") as f:
            json.dump(data, f, indent=4)

        # change status for next instance
        self._in_progress = False
