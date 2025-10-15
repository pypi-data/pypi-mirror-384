"""
arthub_api.blade_api
~~~~~~~~~~~~~~

This module encapsulates the API for blade tool system.
"""
import copy
from contextlib import contextmanager
from .open_api import (
    OpenAPI
)
from . import arthub_api_config
from .config import api_config_oa
from .utils import get_config_by_name


class BladeAPI(OpenAPI):
    def __init__(self, config=api_config_oa, get_token_from_cache=True, blade_public_token="", api_config_name=None):
        r"""Used to call Blade openapi.

        :param config: from arthub_api.config.
        :param get_token_from_cache: read token from local cache.
        """
        super(BladeAPI, self).__init__(config, get_token_from_cache, api_config_name=api_config_name)
        self._api_version_blade = "v1"
        self.blade_public_token = blade_public_token
        
    @contextmanager
    def switch_config(self, api_config_name, get_token_from_cache=True, blade_public_token=""):
        config = get_config_by_name(api_config_name, api_config_oa)
        old__dict = copy.copy(self.__dict__)
        self.__dict__ = BladeAPI(config, get_token_from_cache, blade_public_token).__dict__.copy()
        yield
        self.__dict__ = old__dict

    def init_from_config(self):
        super(BladeAPI, self).init_from_config()
        self.blade_public_token = arthub_api_config.blade_public_token

    def _blade_url(self, api_method):
        return "%s//%s/blade/blade/openapi/%s/core/%s" % (
            self.http_scheme, self.api_host, self._api_version_blade, api_method)

    def _blade_thm_url(self, api_method):
        return "%s//%s/blade/blade/openapi/%s/thm/%s" % (
            self.http_scheme, self.api_host, self._api_version_blade, api_method)

    def _blade_resolving_url(self, api_method):
        return "%s//%s/resolving/resolving/openapi/%s/core/%s" % (
            self.http_scheme, self.api_host, self._api_version_blade, api_method)

    def _blade_resolving_sign_url(self, api_method):
        return "%s//%s/resolving/resolving/openapi/%s/sign/%s" % (
            self.http_scheme, self.api_host, self._api_version_blade, api_method)

    def add_headers(self, headers):
        if self.blade_public_token != "":
            headers["blade-public-token"] = self.blade_public_token

    def has_credential(self):
        r"""Checks if credential is already set or not for Blade"""
        # public_token from pan is not valid credential for blade
        if self.blade_public_token:
            return True
        if self._cookies:
            return True
        if self._token:
            return True
        return False

    def set_blade_public_token(self, token):
        self.blade_public_token = token

    def clear_blade_public_token(self):
        self.blade_public_token = ""

    # root
    def blade_get_root_id(self):
        r"""get the root id of tool space.

        :rtype: arthub_api.APIResponse
                result: 123
        """

        url = self._blade_url("get-root-id")
        res = self._make_api_request(url)
        res.set_result_by_key("id")
        return res

    def blade_get_type_option_info(self):
        r"""get all the type options of tool.

        :rtype: arthub_api.APIResponse
                result: [
                    {
                        "id": 2,
                        "chinese_name": "dcc",
                        "english_name": "dcc",
                        "is_default": false
                    },
                    {
                        "id": 1,
                        "chinese_name": "Other",
                        "english_name": "Other",
                        "is_default": true
                    }
                ]
        """

        url = self._blade_url("get-type-option-info")
        return self._make_api_request(url)

    def blade_set_type_option_info(self, types):
        r"""set all the type options of tool.
        :param types: list. Example:
            [{
                "chinese_name": "art",
                "english_name": "art",
            }]
        :rtype: arthub_api.APIResponse
        """
        req_payload = {
            "items": types
        }
        url = self._blade_url("set-type-option-info")
        return self._make_api_request(url, req_payload)

    # node
    def blade_get_node_brief_by_id(self, items):
        r"""
        :param items: list. Example:
            [{
                "id": 123,
                "parent_id": 456,
            }]
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("get-node-brief-by-id")
        req_payload = {
            "items": items
        }
        return self._make_api_request(url, req_payload)

    def blade_delete_node_brief_by_id(self, items):
        r"""
        :param items: list. Example:
            [{
                "id": 123,
                "parent_id": 456,
            }]
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("delete-node-by-id")
        req_payload = {
            "items": items
        }
        return self._make_api_request(url, req_payload)

    def blade_get_child_node_brief_in_range(self, parent_id, offset=0, count=-1, type_option_id=-1, search_name="",
                                            order_meta="", order_type=""):
        r"""
        :param parent_id: int. Example: 1234.
        :param offset: int. range offset, Example: 0.
        :param count: int. range count, Example: -1.
        :param type_option_id: int. tool type id, Example: -1.
        :param search_name: str. Example: "".
        :param order_meta: str. Example: "updated_date".
        :param order_type: str. Example: "asc".
        :rtype: arthub_api.APIResponse
                result: [
                    {
                        "id": 99120641219446,
                        "type": "toolbox",
                        "short_name": "dmo",
                        "creator": "joeyding"
                    }
                ]
        """
        url = self._blade_url("get-child-node-brief-in-range")
        req_payload = {
            "parent_id": parent_id,
            "offset": offset,
            "count": count,
            "search_name": search_name,
            "type_option_id": type_option_id,
        }
        if order_meta != "" and order_type != "":
            req_payload["order"] = {
                "meta": order_meta,
                "type": order_type
            }
        return self._make_api_request(url, req_payload)

    def blade_get_child_node_count(self, parent_id, type_option_id=-1, search_name=""):
        r"""
        :param parent_id: int. Example: 1234.
        :param type_option_id: int. tool type id, Example: -1.
        :param search_name: str. Example: "".
        :rtype: arthub_api.APIResponse
                result: 1
        """
        url = self._blade_url("get-child-node-count")
        req_payload = {
            "parent_id": parent_id,
            "search_name": search_name,
            "type_option_id": type_option_id,
        }
        res = self._make_api_request(url, req_payload)
        res.set_result_by_key("count")
        return res

    # toolbox
    def blade_create_toolbox(self, payload):
        r"""
        :param payload: dict. Example:
            {
                "parent_id": 123,
                "name": "test_name",
                "description": "toolbox for sdk test",
                "short_name": "test_short_name",
                "public": False
            }
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("create-toolbox")
        res = self._make_api_request(url, payload)
        res.set_result_by_key("id")
        return res

    def blade_update_toolbox(self, payload):
        r"""
        :param payload: dict. Example:
            {
                "id": 123,
                "name": "sdk_test_name_2",
                "description": "toolbox for sdk test 2",
                "short_name": "sdk_test_short_name_2",
                "public": True
            }
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("update-toolbox-by-id")
        return self._make_api_request(url, payload)

    # tool
    def blade_create_tool(self, payload):
        r"""
        :param payload: dict. Example:
            {
                "parent_id": 123,
                "name": "sdk_test_name",
                "description": "tool for sdk test",
                "command": "test command",
                "command_type": "python",
                "drag_hook": True,
                "drag_hook_command": "test hook command",
                "drag_hook_type": "cmd",
                "type_option": 1,
                "flag_color": "red",
                "flag_content": "2020",
            }
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("create-tool")
        res = self._make_api_request(url, payload)
        res.set_result_by_key("id")
        return res

    def blade_update_tool(self, payload):
        r"""
        :param payload: dict. Example:
            {
                "id": 123,
                "name": "sdk_test_name_2",
                "description": "tool for sdk test 2",
                "command": "test command 2",
                "command_type": "cmd",
                "type_option": 2,
                "flag_color": "blue",
                "flag_content": "2022",
            }
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("update-tool-by-id")
        return self._make_api_request(url, payload)

    def blade_move_tool(self, ids, parent_id, other_parent_id):
        r"""
        :param ids: list. Example: [123, 345]
        :param parent_id: int. Example: 123
        :param other_parent_id: int. Example: 456

        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("move-tool")
        return self._make_api_request(url, {
            "ids": ids,
            "parent_id": parent_id,
            "other_parent_id": other_parent_id
        })

    def blade_share_tool(self, ids, parent_id, other_parent_id):
        r"""
        :param ids: list. Example: [123, 345]
        :param parent_id: int. Example: 123
        :param other_parent_id: int. Example: 456

        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("share-tool")
        return self._make_api_request(url, {
            "ids": ids,
            "parent_id": parent_id,
            "other_parent_id": other_parent_id
        })

    # user
    def blade_create_user(self, user_info, upsert=False):
        r"""
        :param user_info: dict. Example: {
                    "id": 123,
                    "qywxalias": "joey",
                    "email": "12345@qq.com",
                    "fullname": "joey",
                    "position": "dev",
                }
        :param upsert: bool. Example: false
        :rtype: arthub_api.APIResponse
                result: 123
        """
        url = self._blade_url("create-user")
        res = self._make_api_request(url, {
            "user": user_info,
            "upsert": upsert
        })
        res.set_result_by_key("id")
        return res

    def blade_update_user_by_id(self, payload):
        r"""
        :param payload: dict. Example: {
                    "id": 123,
                    "email": "12345@qq.com",
                    "fullname": "joey",
                    "position": "dev",
                }
        :rtype: arthub_api.APIResponse
                result: 123
        """
        url = self._blade_url("update-user-by-id")
        res = self._make_api_request(url, payload)
        res.set_result_by_key("id")
        return res

    def blade_get_user_by_id(self, account_id):
        r"""
        :param account_id: int. Example: 123
        :rtype: arthub_api.APIResponse
                result: {
                    "account": {"id": 123, "nick_name": "joey", ...},
                    "id": 123,
                    "name": "joey",
                    "created_date": "2023-05-09 14:33:34",
                    ...,
                }
        """
        url = self._blade_url("get-user")
        res = self._make_api_request(url, {"id": account_id})
        res.set_result_by_key("user")
        return res

    def blade_get_user_by_qywx_alias(self, qywx_alias):
        r"""
        :param qywx_alias: str. Example: "joey"
        :rtype: arthub_api.APIResponse
                result: {
                    "account": {"id": 123, "nick_name": "joey", ...},
                    "id": 123,
                    "name": "joey",
                    "created_date": "2023-05-09 14:33:34",
                    ...,
                }
        """
        url = self._blade_url("get-user")
        res = self._make_api_request(url, {"qywxalias": qywx_alias})
        res.set_result_by_key("user")
        return res

    def blade_list_user(self):
        r"""
        :rtype: arthub_api.APIResponse
                result: [{
                    "id": 123,
                    "name": "joey",
                    "created_date": "2023-05-09 14:33:34",
                    ...,
                }]
        """
        url = self._blade_url("list-user")
        res = self._make_api_request(url)
        res.set_result_by_key("users")
        return res

    def blade_delete_user_by_id(self, account_id):
        r"""
        :param account_id: int. Example: 123
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("delete-user-by-id")
        return self._make_api_request(url, {"id": account_id})

    # config
    def blade_create_config(self, name, context_id, context_type, config, upsert=True):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :param config: dict. Example: {"env": 1}
        :param upsert: bool. Example: True
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("create-config")
        return self._make_api_request(url, {
            "upsert": upsert,
            "config": {
                "name": name,
                "context_id": context_id,
                "context_type": context_type,
                "config": config
            }
        })

    def blade_update_config(self, name, context_id, context_type, config):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :param config: dict. Example: {"env": 1}
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("update-config")
        return self._make_api_request(url, {
            "name": name,
            "context_id": context_id,
            "context_type": context_type,
            "config": config
        })

    def blade_get_config(self, name, context_id, context_type):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :rtype: arthub_api.APIResponse
                result: {
                    "name": "test_sdk",
                    "context_id": 123,
                    "context_type": "node",
                    "config": {"env": 1}
                    ...,
                }
        """
        url = self._blade_url("get-config")
        res = self._make_api_request(url, {"name": name, "context_type": context_type, "context_id": context_id})
        res.set_result_by_key("config")
        return res

    def blade_batch_get_config(self, names, depot_id=[], toolbox_id=[], role_id=[], empty_role=False):
        r"""
        :param names: str. Example: ["test_sdk", "test_sdk_2"].
        :param depot_id: int. Example: [123, 456].
        :param toolbox_id: int. Example: [123, 456].
        :param role_id: int. Example: [123, 456].
        :param empty_role: bool. Example: True.
        :rtype: arthub_api.APIResponse
                result: [{
                    "name": "test_sdk",
                    "context_id": 123,
                    "context_type": "node",
                    "config": {"env": 1}
                    ...,
                }]
        """
        url = self._blade_url("batch-get-config")
        res = self._make_api_request(url, {"names": names,
                                           "depot_id": depot_id,
                                           "toolbox_id": toolbox_id,
                                           "role_id": role_id,
                                           "empty_role": empty_role})
        res.set_result_by_key("configs")
        return res

    def blade_delete_config(self, name, context_id, context_type):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("delete-config")
        return self._make_api_request(url, {"name": name, "context_type": context_type, "context_id": context_id})

    # plugin
    def blade_create_plugin(self, name, context_id, context_type, plugin_info, upsert=True):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :param plugin_info: dict. Example: {
                    "runnable": True,
                    "shellable": True,
                    "short_help": "start test",
                    "packages": [
                        "maya-20201",
                        "maya_tony_master-2"
                    ]
                }
        :param upsert: bool. Example: True
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("create-plugin")
        plugin_info["name"] = name
        plugin_info["context_id"] = context_id
        plugin_info["context_type"] = context_type
        req_payload = {
            "upsert": upsert,
            "plugin": plugin_info,
        }
        return self._make_api_request(url, req_payload)

    def blade_update_plugin(self, name, context_id, context_type, plugin_update_payload):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :param plugin_update_payload: dict. Example: {
                                        "runnable": True,
                                        "shellable": True,
                                        "short_help": "start test",
                                        "is_packages_change": True,
                                        "packages": [
                                            "maya-20201",
                                            "maya_tony_master-2"
                                        ]
                                    }
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("update-plugin")
        req_payload = plugin_update_payload
        req_payload["name"] = name
        req_payload["context_id"] = context_id
        req_payload["context_type"] = context_type

        return self._make_api_request(url, req_payload)

    def blade_get_plugin(self, name, context_id, context_type):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :rtype: arthub_api.APIResponse
                result: {
                    "name": "sdk_test_plugin",
                    "context_id": 123,
                    "context_type": "node",
                    "command": "command_Test",
                    "runnable": true,
                    "short_help": "start test",
                    "packages": [
                        "pkg1",
                        "pkg2"
                    ],
                    ...,
                }
        """
        url = self._blade_url("get-plugin")
        res = self._make_api_request(url, {"name": name, "context_type": context_type, "context_id": context_id})
        res.set_result_by_key("plugin")
        return res

    def blade_batch_get_plugin(self, names, depot_id=[], toolbox_id=[], role_id=[], empty_role=False):
        r"""
        :param names: str. Example: ["test_sdk", "test_sdk_2"].
        :param depot_id: int. Example: [123, 456].
        :param toolbox_id: int. Example: [123, 456].
        :param role_id: int. Example: [123, 456].
        :param empty_role: bool. Example: True.
        :rtype: arthub_api.APIResponse
                result: [{
                    "name": "test_sdk",
                    "context_id": 123,
                    "context_type": "node",
                    "command": "command_Test",
                    "runnable": true,
                    "short_help": "start test",
                    "packages": [
                        "pkg1",
                        "pkg2"
                    ],
                    ...,
                }]
        """
        url = self._blade_url("batch-get-plugin")
        res = self._make_api_request(url, {"names": names,
                                           "depot_id": depot_id,
                                           "toolbox_id": toolbox_id,
                                           "role_id": role_id,
                                           "empty_role": empty_role})
        res.set_result_by_key("plugins")
        return res

    def blade_delete_plugin(self, name, context_id, context_type):
        r"""
        :param name: str. Example: "test_sdk".
        :param context_id: int. Example: 123.
        :param context_type: str. Example: "node" || "role".
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("delete-plugin")
        return self._make_api_request(url, {"name": name, "context_type": context_type, "context_id": context_id})

    # public token
    def blade_create_public_token(self, fullname, duration):
        r"""
        :param fullname: str. Example: sdk_test_token
        :param duration: int. Example: 100
        :param upsert: bool. Example: True
        :rtype: arthub_api.APIResponse
                result: {
                    "id": 123,
                    "name": XXX
                }
        """
        url = self._blade_url("create-public-token")
        res = self._make_api_request(url, {
            "token": {
                "fullname": fullname,
                "duration": duration
            }
        })
        res.set_result_as_first_item()
        return res

    def blade_update_public_token_by_id(self, payload):
        r"""
        :param payload: dict. Example: {
                    "id": 123,
                    "fullname": "sdk_test_token",
                    "status": "normal",
                    "duration": -1
                }
        :rtype: arthub_api.APIResponse
                result: 123
        """
        url = self._blade_url("update-public-token-by-id")
        res = self._make_api_request(url, payload)
        res.set_result_by_key("id")
        return res

    def blade_get_public_token_by_id(self, token_id):
        r"""
        :param token_id: int. Example: 123
        :rtype: arthub_api.APIResponse
                result: {
                    "id": 123,
                    "name": "XXX",
                    "created_date": "2023-05-09 18:50:18",
                    "creator": "joeyding",
                    "fullname": "sdk_test_token",
                    "duration": 100,
                    "status": "normal"
                }
        """
        url = self._blade_url("get-public-token")
        res = self._make_api_request(url, {"id": token_id})
        res.set_result_by_key("token")
        return res

    def blade_get_public_token_by_name(self, name):
        r"""
        :param name: str. Example: "XXX"
        :rtype: arthub_api.APIResponse
                result: {
                    "id": 123,
                    "name": "XXX",
                    "created_date": "2023-05-09 18:50:18",
                    "creator": "joeyding",
                    "fullname": "sdk_test_token",
                    "duration": 100,
                    "status": "normal"
                }
        """
        url = self._blade_url("get-public-token")
        res = self._make_api_request(url, {"name": name})
        res.set_result_by_key("token")
        return res

    def blade_list_public_token(self):
        r"""
        :rtype: arthub_api.APIResponse
                result: [{
                    "id": 123,
                    "name": "XXX",
                    "created_date": "2023-05-09 18:50:18",
                    "creator": "joeyding",
                    "fullname": "sdk_test_token",
                    "duration": 100,
                    "status": "normal"
                }]
        """
        url = self._blade_url("list-public-token")
        res = self._make_api_request(url)
        res.set_result_by_key("tokens")
        return res

    def blade_delete_public_token_by_id(self, token_id):
        r"""
        :param token_id: int. Example: 123
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("delete-public-token-by-id")
        return self._make_api_request(url, {"id": token_id})

    # permission toolbox
    def blade_get_permission_on_toolbox(self, toolbox_id):
        r"""
        :param toolbox_id: int. Example: 123
        :rtype: arthub_api.APIResponse
                result: {
                    "admin": [{"account_name": "joey", "type": "person"}],
                    "developer": [],
                    "guest": []
                }
        """
        url = self._blade_url("get-permission-on-toolbox")
        res = self._make_api_request(url, {"id": toolbox_id})
        res.set_result_by_key("permission")
        return res

    def blade_delete_permission_on_toolbox_by_account_name(self, toolbox_id, accounts):
        r"""
        :param toolbox_id: int. Example: 123
        :param accounts: list. Example: [{"account_name": "joey", "type": "person"}]
        :rtype: arthub_api.APIResponse
                result: [{"account_name": "joey", "type": "person"}]
        """
        url = self._blade_url("delete-permission-on-toolbox-by-account-name")
        res = self._make_api_request(url, {"id": toolbox_id, "accounts": accounts})
        res.set_result_by_key("accounts")
        return res

    def blade_add_permission_on_toolbox_by_account_name(self, toolbox_id, permission, accounts):
        r"""
        :param toolbox_id: int. Example: 123
        :param permission: str. Example: "developer"
        :param accounts: list. Example: [{"account_name": "joey", "type": "person"}]
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("add-permission-on-toolbox-by-account-name")
        return self._make_api_request(url, {"id": toolbox_id, "permission": permission, "accounts": accounts})

    # permission toolbox
    def blade_get_permission_on_config(self):
        r"""
        :rtype: arthub_api.APIResponse
                result: {
                    "admin": [{"account_name": "joey", "type": "person"}],
                    "developer": [],
                    "guest": []
                }
        """
        url = self._blade_url("get-permission-on-config")
        res = self._make_api_request(url)
        res.set_result_by_key("permission")
        return res

    def blade_delete_permission_on_config_by_account_name(self, accounts):
        r"""
        :param accounts: list. Example: [{"account_name": "joey", "type": "person"}]
        :rtype: arthub_api.APIResponse
                result: [{"account_name": "joey", "type": "person"}]
        """
        url = self._blade_url("delete-permission-on-config-by-account-name")
        res = self._make_api_request(url, {"accounts": accounts})
        res.set_result_by_key("accounts")
        return res

    def blade_add_permission_on_config_by_account_name(self, permission, accounts):
        r"""
        :param permission: str. Example: "developer"
        :param accounts: list. Example: [{"account_name": "joey", "type": "person"}]
        :rtype: arthub_api.APIResponse
        """
        url = self._blade_url("add-permission-on-config-by-account-name")
        return self._make_api_request(url, {"permission": permission, "accounts": accounts})

    def blade_convert_context_string(self, context, app):
        r"""
        :param context: str. Example: "globals:globals", "project:dmo", "etc/project/dmo", ...
        :param app: str. one of ["lightbox_config", "thm_plugins"]
        """
        url = self._blade_thm_url("convert-context-string")
        res = self._make_api_request(url, {"context": context, "app": app})
        return res

    def blade_create_package(self, package, upsert=False):
        r"""
        :param package: dict. Example: {
            "name": "arthub_test_pkg",
            "version": "0.0.1",
            "authors": [
                "Guido van Rossum"
            ],
            "category": "ext",
            "description": "The Python programming language.",
            "homepage": "https://www.python.org/",
            "requires": [],
            "tools": [
                "arthub_tester"
            ],
            "variants": [
                [
                    "platform-windows",
                    "python_embedded"
                ],
                [
                    "platform-windows",
                    "!python_embedded"
                ]
            ]
        }
        :param upsert: bool. Example: false. Default false
        :rtype: arthub_api.APIResponse
            nothing is returned if success
        """
        url = self._blade_resolving_url("create-package")
        return self._make_api_request(url, {"package": package, "upsert": upsert})

    def blade_update_package(self, name, version, homepage=None, description=None,
                             category=None, authors=None, requires=None, tools=None, variants=None,
                             ):
        r"""
        :param name: str. must pass this param
        :param version: str. must pass this param
        :param homepage: str.
        :param description: str.
        :param category: str.
        :param authors: List[str].
        :param requires: List[str].
        :param tools: List[str].
        :param variants: List[List[str]]
            see example value in get_package api
        :rtype: arthub_api.APIResponse
            nothing is returned if success
        """
        req = {
            "name": name,
            "version": version,
        }
        if homepage is not None:
            req.update({"homepage": homepage})
        if description is not None:
            req.update({"description": description})
        if category is not None:
            req.update({"category": category})
        if authors is not None:
            req.update({"is_authors_change": True, "authors": authors})
        if requires is not None:
            req.update({"is_requires_change": True, "requires": requires})
        if tools is not None:
            req.update({"is_tools_change": True, "tools": tools})
        if variants is not None:
            req.update({"is_variants_change": True, "variants": variants})
        url = self._blade_resolving_url("update-package")
        return self._make_api_request(url, req)

    def blade_get_package(self, name, version):
        r"""
        :param name: str. must pass this param
        :param version: str. must pass this param
        :rtype: arthub_api.APIResponse
            result: {
                "depot_id": 99120641218000,
                "name": "arthub_test_pkg",
                "version": "0.0.1",
                "api_modified": "2023-04-26 03:43:02",
                "authors": [
                    "Guido van Rossum"
                ],
                "homepage": "https://www.python.org/",
                "description": "The Python programming language.",
                "tools": [
                    "python"
                ],
                "category": "ext",
                "variants": [
                    [
                        "platform-windows",
                        "python_embedded"
                    ],
                    [
                        "platform-windows",
                        "!python_embedded"
                    ]
                ],
                "creator": "joeyding"
            }
        """
        url = self._blade_resolving_url("get-package")
        res = self._make_api_request(url, {"name": name, "version": version})
        res.set_result_by_key("package")
        return res

    def blade_search_package(self, name):
        r"""
        :param name: str. name is treated as regexp format
        :rtype: arthub_api.APIResponse
            [{pkg...}, {pkg...}]
            see package structure in above get_package api
        """
        url = self._blade_resolving_url("search-package")
        res = self._make_api_request(url, {"name": name})
        res.set_result_by_key("packages")
        return res

    def blade_upload_package(self, packages, force=False):
        r"""
        :param packages: List[dict]. [{"name": str, "version": str}, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{"signed_url": str, "origin_url": str}, ...]
            result length should match input packages length.
            signed_url is used for PUT request, see more at s3 PutObject
        """
        url = self._blade_resolving_url("upload-package")
        return self._make_api_request(url, {"packages": packages, "force": force})

    def blade_begin_multipart_package_upload(self, packages, force=False):
        r"""
        :param packages: List[dict]. [{"name": str, "version": str}, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{"signed_url": str, "origin_url": str}, ...]
            result length should match input packages length.
            signed_url is used for POST request, see more at s3 CreateMultipartUpload
            after POST request, you should obtain a `upload_id` str
        """
        url = self._blade_resolving_url("begin-multipart-package-upload")
        return self._make_api_request(url, {"packages": packages, "force": force})

    def blade_part_package_upload(self, packages, force=False):
        r"""
        :param packages: List[dict]. 
            [{
                "name": str, 
                "version": str,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c",
                "part_number":1
            }, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{
                "signed_url": str, 
                "origin_url": str,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c",
                "part_number":1
            }, ...]
            result length should match input packages length.
            part_number starts from 1.
            signed_url is used for PUT request, see more at s3 UploadPart
            after PUT request, you should obtain a `ETag` header for this part
        """
        url = self._blade_resolving_url("part-package-upload")
        return self._make_api_request(url, {"packages": packages, "force": force})

    def blade_complete_multipart_package_upload(self, packages, force=False):
        r"""
        :param packages: List[dict].
            [{
                "name": str, 
                "version": str,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c",
            }, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{
                "signed_url": str, 
                "origin_url": str,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c"
            }, ...]
            result length should match input packages length.
            signed_url is used for POST request, see more at s3 CompleteMultipartUpload
            ETag and PartNumber should be set in POST body
        """
        url = self._blade_resolving_url("complete-multipart-package-upload")
        return self._make_api_request(url, {"packages": packages, "force": force})

    def blade_download_package(self, packages):
        r"""
        :param packages: List[dict].
            [{
                "name": str, 
                "version": str
            }, ...]
        :rtype: arthub_api.APIResponse
            [{
                "signed_url": str, 
                "origin_url": str,
                "size": 1601
            }, ...]
            size is bytes size of existed file, useful for multipart download
        """
        url = self._blade_resolving_url("download-package")
        return self._make_api_request(url, {"packages": packages})

    def blade_get_rez_repo(self, force_refresh=False):
        r"""
        :param packages: force_refresh: bool.  indicates whether to refresh rez_repo with the latest package info
        :rtype: arthub_api.APIResponse
            {
                "data": {
                    "pkg_name": {
                        "pkg_version1": {...},
                        "pkg_version2": {...},
                    }
                 },
                "api_modified": "xxxx"
            }
            leaf object contains {name, version, requires, variants}
        """
        url = self._blade_resolving_url("get-rez-repo")
        res = self._make_api_request(url, {"refresh": force_refresh})
        res.set_result_as_first_item()
        return res

    def blade_get_package_count(self):
        r"""
        :rtype: arthub_api.APIResponse
            result: (number) count of packages
        """
        url = self._blade_resolving_url("get-package-count")
        res = self._make_api_request(url, {})
        res.set_result_by_key("count")
        return res

    def blade_upload_sign(self, items, force=False):
        r"""
        :param items: List[dict]. [{"cos_key": str, "expired": 1200}, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{"signed_url": str, "origin_url": str}, ...]
            result length should match input items length.
            signed_url is used for PUT request, see more at s3 PutObject
        """
        url = self._blade_resolving_sign_url("upload")
        return self._make_api_request(url, {"items": items, "force": force})

    def blade_begin_multipart_upload_sign(self, items, force=False):
        r"""
        :param items: List[dict]. [{"cos_key": str, "expired": 1200}, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{"signed_url": str, "origin_url": str}, ...]
            result length should match input items length.
            signed_url is used for POST request, see more at s3 CreateMultipartUpload
            after POST request, you should obtain a `upload_id` str
        """
        url = self._blade_resolving_sign_url("begin-multipart-upload")
        return self._make_api_request(url, {"items": items, "force": force})

    def blade_part_upload_sign(self, items, force=False):
        r"""
        :param items: List[dict]. 
            [{
                "cos_key": str,
                "expired": 1200,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c",
                "part_number":1
            }, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{
                "signed_url": str, 
                "origin_url": str,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c",
                "part_number":1
            }, ...]
            result length should match input items length.
            part_number starts from 1.
            signed_url is used for PUT request, see more at s3 UploadPart
            after PUT request, you should obtain a `ETag` header for this part
        """
        url = self._blade_resolving_sign_url("part-upload")
        return self._make_api_request(url, {"items": items, "force": force})

    def blade_complete_multipart_upload_sign(self, items, force=False):
        r"""
        :param items: List[dict].
            [{
                "cos_key": str,
                "expired": 1200,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c",
            }, ...]
        :param force: bool. example: false. default: false
        :rtype: arthub_api.APIResponse
            [{
                "signed_url": str, 
                "origin_url": str,
                "upload_id": "16835262901cf8ebac376ade701dd7ce4ce881a32799ab71ad2297f4ef8660a9f68d9e6d2c"
            }, ...]
            result length should match input items length.
            signed_url is used for POST request, see more at s3 CompleteMultipartUpload
            ETag and PartNumber should be set in POST body
        """
        url = self._blade_resolving_sign_url("complete-multipart-upload")
        return self._make_api_request(url, {"items": items, "force": force})

    def blade_download_sign(self, items):
        r"""
        :param items: List[dict].
            [{
                "cos_key": str,
                "expired": 1200
            }, ...]
        :rtype: arthub_api.APIResponse
            [{
                "signed_url": str, 
                "origin_url": str,
                "size": 1601
            }, ...]
            size is bytes size of existed file, useful for multipart download
        """
        url = self._blade_resolving_sign_url("download")
        return self._make_api_request(url, {"items": items})