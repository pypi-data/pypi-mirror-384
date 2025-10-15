# -*- encoding: utf-8 -*-
"""
Copyright (c) 2025

This module contains poller.

"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
from urllib.parse import urlencode, urljoin

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

from .const import *
from .exception import *
from .utils import ParserHelper, Validator, AlternativeParserHelper

logger = logging.getLogger(__name__)


class GeneratorInfo(object):
    def __init__(
        self,
        collection_name,
        session_type,
        date_from=None,
        date_to=None,
        query=None,
        limit=None,
        keys=None,
        iocs_keys=None,
        ignore_validation=False,
    ):
        self.collection_name = collection_name
        self.session_type = session_type
        self.date_from = date_from
        self.date_to = date_to
        self.query = query
        self.limit = limit
        self.keys = keys
        self.iocs_keys = iocs_keys
        self.ignore_validation = ignore_validation

        self._validate_default_fields()

    def _validate_default_fields(self, collections_info=None) -> None:
        """
        Function for field validation. Should be called during initialization.
        """
        if self.ignore_validation:
            return
        Validator.validate_collection_name(
            self.collection_name, method=self.session_type
        )
        if collections_info:
            if self.date_from:
                Validator.validate_date_format(
                    date=self.date_from,
                    formats=collections_info.get(self.collection_name).get(
                        "date_formats"
                    ),
                )
            if self.date_to:
                Validator.validate_date_format(
                    date=self.date_to,
                    formats=collections_info.get(self.collection_name).get(
                        "date_formats"
                    ),
                )

        if self.limit:
            int(self.limit)


class TIGeneratorInfo(GeneratorInfo):
    def __init__(
        self,
        collection_name,
        session_type,
        date_from=None,
        date_to=None,
        query=None,
        limit=None,
        keys=None,
        iocs_keys=None,
        ignore_validation=False,
        apply_hunting_rules=None,
        parse_events=None,
        is_tailored=None,
        apply_has_exploit=None,
        probable_corporate_access=None,
        unique=None,
        combolist=None,
    ):
        self.apply_hunting_rules = apply_hunting_rules
        self.parse_events = parse_events
        self.is_tailored = is_tailored
        self.apply_has_exploit = apply_has_exploit
        self.probable_corporate_access = probable_corporate_access
        self.unique = unique
        self.combolist = combolist

        super().__init__(
            collection_name=collection_name,
            session_type=session_type,
            date_from=date_from,
            date_to=date_to,
            query=query,
            limit=limit,
            keys=keys,
            iocs_keys=iocs_keys,
            ignore_validation=ignore_validation,
        )

    def _validate_default_fields(
        self, collections_info=CollectionConsts.TI_COLLECTIONS_INFO
    ):
        super()._validate_default_fields(
            collections_info=CollectionConsts.TI_COLLECTIONS_INFO
        )
        if self.apply_hunting_rules is not None:
            try:
                if self.apply_hunting_rules not in [0, 1]:
                    raise BaseException
            except BaseException as e:
                logger.exception(
                    "Wrong apply_hunting_rules input it should be '0' or '1'"
                )

        if self.is_tailored is not None:
            try:
                if self.is_tailored not in [0, 1]:
                    raise ValueError
            except ValueError:
                logger.exception(
                    "Wrong is_tailored input, it should be '0' or '1'."
                )

        if self.apply_has_exploit is not None:
            try:
                if self.apply_has_exploit not in [0, 1]:
                    raise ValueError
            except ValueError:
                logger.exception(
                    "Wrong apply_has_exploit input, it should be '0' or '1'."
                )

        if self.probable_corporate_access is not None:
            try:
                if self.probable_corporate_access not in [0, 1]:
                    raise ValueError
            except ValueError:
                logger.exception(
                    "Wrong probable_corporate_access input, it should be '0' or '1'."
                )

        if self.unique is not None:
            try:
                if self.unique not in [0, 1]:
                    raise ValueError
            except ValueError:
                logger.exception(
                    "Wrong unique input, it should be '0' or '1'."
                )

        if self.combolist is not None:
            try:
                if self.combolist not in [0, 1]:
                    raise ValueError
            except ValueError:
                logger.exception(
                    "Wrong combolist input, it should be '0' or '1'."
                )


class DRPGeneratorInfo(GeneratorInfo):
    def __init__(
        self,
        collection_name,
        session_type,
        date_from=None,
        date_to=None,
        query=None,
        limit=None,
        keys=None,
        iocs_keys=None,
        ignore_validation=False,
        subtypes=None,
        section=None,
        brands=None,
        use_typo_squatting=None,
        approve_states=None,
    ):

        self.subtypes = subtypes
        self.section = section
        self.brands = brands
        self.use_typo_squatting = use_typo_squatting
        self.approve_states = approve_states

        super().__init__(
            collection_name=collection_name,
            session_type=session_type,
            date_from=date_from,
            date_to=date_to,
            query=query,
            limit=limit,
            keys=keys,
            iocs_keys=iocs_keys,
            ignore_validation=ignore_validation,
        )

    def _validate_default_fields(
        self, collections_info=CollectionConsts.DRP_COLLECTIONS_INFO
    ):
        super()._validate_default_fields(
            collections_info=CollectionConsts.DRP_COLLECTIONS_INFO
        )


class Poller(object):
    """
    Poller that can be used for requests to TI.

    :param str username: Login for TI.
    :param str api_key: API key, generated in TI.
    :param str api_url: (optional) URL for TI.
    """

    def __init__(self, username, api_key, api_url):
        # type: (str, str, str) -> None

        """
        :param username: Login.
        :param api_key: API key, generated in profile.
        """
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(username, api_key)
        self._session.headers.update(RequestConsts.HEADERS)
        self._session.verify = False
        self._username = username
        self._api_url = api_url
        self._keys = {}
        self._iocs_keys = {}
        self._mount_adapter_with_retries()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    def _mount_adapter_with_retries(
        self,
        retries=RequestConsts.RETRIES,
        backoff_factor=RequestConsts.BACKOFF_FACTOR,
        status_forcelist=RequestConsts.STATUS_CODE_FORCELIST,
    ):
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _status_code_handler(self, response):
        # type: (Response) -> None

        status_code = response.status_code
        if status_code == 200:
            return
        elif status_code in RequestConsts.STATUS_CODE_MSGS:
            raise ConnectionException(
                f"Status code: {status_code}. Message: {RequestConsts.STATUS_CODE_MSGS[status_code]}"
            )
        else:
            raise ConnectionException(
                f"Something wrong. Status code: {status_code}. Response body: {response.text}."
            )

    def send_request(
        self,
        endpoint,
        method="GET",
        data=None,
        params=None,
        decode=True,
        **kwargs,
    ):
        # type: (str, Union['GET', 'POST'] , Optional[dict], Optional[dict], bool, Any) -> Any
        """
        Send request based on endpoint and custom params

        :param endpoint: the endpoint will be applied to the existing base URL (api_url) using the urljoin.
        :param method: HTTP method ('GET' or 'POST').
        :param data: dict-like object with data to be sent in the request body for POST requests.
        :param params: dict-like object with params which will be set using the urlencode for GET requests.
        :param decode: decode output in JSON (True) or leave as plain text (False). By default, set to True.
        """

        url = urljoin(self._api_url, endpoint)
        params = urlencode({k: v for k, v in (params or {}).items() if v})

        methods = {
            "GET": self._session.get,
            "POST": self._session.post,
        }

        try:
            response = methods.get(method.upper())(
                url,
                data=data,
                params=params,
                timeout=RequestConsts.TIMEOUT,
                proxies=self._session.proxies,
                **kwargs,
            )

            response_status_code = response.status_code
            response_headers = response.headers
            response_encoding = response.encoding
            logger.info(f"Response Status Code: {response_status_code}")
            logger.info(f"Response Headers: {response_headers}")
            logger.info(f"Detected Encoding: {response_encoding}")

            self._status_code_handler(response)
            if decode:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(
                        f"""
                        An error occurred while decoding the json response to a request to {response.url} \n
                        Response Status Code: {response_status_code} \n
                        Response Headers: {response_headers} \n
                        Detected Encoding: {response_encoding} \n
                        The data obtained in the answer: {response.text} \n
                        """
                    )
                    raise ConnectionException(
                        f"""
                        An error occurred while decoding the json response to a request to {response.url} \n
                        Response Status Code: {response_status_code} \n
                        Response Headers: {response_headers} \n
                        Detected Encoding: {response_encoding} \n
                        The data obtained in the answer: {response.text} \n
                        """
                    )
            return response.content
        except requests.exceptions.Timeout as e:
            raise ConnectionException(
                f"Max retries reached. Exception message: {e}"
            )

    def set_proxies(
        self,
        proxy_protocol=None,
        proxy_ip=None,
        proxy_port=None,
        proxy_username=None,
        proxy_password=None,
        encrypted_data_handler=None,
    ):
        # type: (Union['http', 'https'], str, str, str, str, Any) -> Union[Dict[str, str], None]
        """
        Method that returns proxies from given arguments. Only HTTP and HTTPS allowed.

            Return format:

            >>> {
            >>>     "http": "{protocol}://{username}:{password}@{ip}:{port}",
            >>>     "https": "{protocol}://{username}:{password}@{ip}:{port}"
            >>> }

        :param proxy_protocol: HTTP or HTTPS
        :param proxy_ip: 255.255.255.255 format
        :param proxy_port: 3128, 3129, ...
        :param proxy_username: Username
        :param proxy_password: Password parametr ignored for secure purpose
        :param encrypted_data_handler: Encryption object engine which is used to decrypt password
        :return: proxies
        """

        if not proxy_protocol or not proxy_ip or not proxy_port:
            return None

        protocol_allowed_list = ["http", "https"]
        proxy_protocol = proxy_protocol.lower()

        if proxy_protocol not in protocol_allowed_list:
            raise BadProtocolError(
                "Bad protocol used for proxy: {protocol}! Expected: {allowed}".format(
                    protocol=proxy_protocol, allowed=protocol_allowed_list
                )
            )

        if encrypted_data_handler:
            try:
                __proxy_password = encrypted_data_handler(
                    label="proxy_password"
                ).decrypt()
            except EncryptionError:
                __proxy_password = None
        else:
            __proxy_password = proxy_password

        if proxy_username and __proxy_password:
            __proxy_dict = {
                "http": "{protocol}://{username}:{password}@{ip}:{port}".format(
                    protocol=proxy_protocol,
                    username=proxy_username,
                    password=__proxy_password,
                    ip=proxy_ip,
                    port=proxy_port,
                ),
                "https": "{protocol}://{username}:{password}@{ip}:{port}".format(
                    protocol=proxy_protocol,
                    username=proxy_username,
                    password=__proxy_password,
                    ip=proxy_ip,
                    port=proxy_port,
                ),
            }
            self._session.proxies = __proxy_dict

        __proxy_dict = {
            "http": "{protocol}://{ip}:{port}".format(
                protocol=proxy_protocol, ip=proxy_ip, port=proxy_port
            ),
            "https": "{protocol}://{ip}:{port}".format(
                protocol=proxy_protocol, ip=proxy_ip, port=proxy_port
            ),
        }

        self._session.proxies = __proxy_dict

    def set_verify(self, verify):
        # type: (Union[bool, str]) -> None

        """
        Sets verify for `Session` object.

        :param verify: Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to ``True``. When set to
            ``False``, requests will accept any TLS certificate presented by
            the server, and will ignore hostname mismatches and/or expired
            certificates, which will make your application vulnerable to
            man-in-the-middle (MitM) attacks. Setting verify to ``False``
            may be useful during local development or testing.
        """
        self._session.verify = verify

    def set_product(
        self,
        product_type="unknown",
        product_name="unknown",
        product_version="unknown",
        integration_name="unknown",
        integration_version="unknown",
    ):
        # type: (Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]) -> None

        def _merge(name, version):
            return (
                "{}_{}".format(name, version) if version != "unknown" else name
            )

        self._session.headers["User-Agent"] = (
            "{product_type}/{product}/{integration}/{username}/{library}".format(
                product_type=product_type,
                product=_merge(product_name, product_version),
                integration=_merge(integration_name, integration_version),
                # default metadata
                username=self._username,
                library=_merge(
                    TechnicalConsts.library_name,
                    TechnicalConsts.library_version,
                ),
            )
        )

    def set_keys(self, collection_name, keys, ignore_validation=False):
        # type: (str, Dict[str, str], Optional[bool]) -> None
        """
        Sets `Keys` to search in the selected collection. It should be python dict where
            key - result name

            value - dot notation string with searchable keys

        Example:
                {"result_name": "searchable_key_1.searchable_key_2"}


        Parser search keys recursively in lists/dicts. If you want to set your own value in result,
        then start with * before the name. You also can make a full template to nest data in the way you want.

        Explore the next sample:

            Your mapping dict:

                >>> {
                >>>     'network': {'ips': 'iocs.network.ip'},
                >>>     'url': 'iocs.network.url',
                >>>     'type': '*custom_network'
                >>> }

            Received feeds:

                >>> [
                >>>     {
                >>>         'iocs': {
                >>>             'network': [
                >>>                 {
                >>>                     'ip': [1, 2],
                >>>                     'url': 'url.com'
                >>>                 },
                >>>                 {
                >>>                     'ip': [3],
                >>>                     'url': ''
                >>>                 }
                >>>             ]
                >>>         }
                >>>     },
                >>>     {
                >>>         'iocs': {
                >>>             'network': [
                >>>                 {
                >>>                     'ip': [4, 5],
                >>>                     'url': 'new_url.com'
                >>>                 }
                >>>             ]
                >>>         }
                >>>     }
                >>> ]

            Resulted output:

                >>> [
                >>>     {
                >>>         'network': {'ips': [[1, 2], [3]]},
                >>>         'url': ['url.com', ''],
                >>>         'type': 'custom_network'
                >>>     },
                >>>     {
                >>>         'network': {'ips': [[4, 5]]},
                >>>         'url': ['new_url.com'],
                >>>         'type': 'custom_network'
                >>>     }
                >>> ]

        :param collection_name: name of the collection to set mapping keys for.
        :param keys: python dict with mapping keys to parse.
        """
        if not ignore_validation:
            Validator.validate_collection_name(collection_name)
            Validator.validate_set_keys_input(keys)
        self._keys[collection_name] = keys

    def set_iocs_keys(self, collection_name, keys, ignore_validation=False):
        # type: (str, Dict[str, str], Optional[bool]) -> None
        """
        Sets keys to search IOCs in the selected collection. `keys` should be the python dict in this format:
        {key_name_you_want_in_result_dict: data_you_want_to_find}. Parser finds keys recursively in lists/dicts
        so set `data_you_want_to_find` using dot notation: ``firstkey.secondkey``.

        For example:
        Keys {'ips': 'iocs.network.ip', 'url': 'iocs.network.url'} for list of feeds:

        [
            {
                'iocs': {
                    'network':
                        [{'ip': [1, 2], 'url': 'url.com'}, {'ip': [3], url: ""}]
                }
            },

            {
                'iocs': {
                    'network':
                        [{'ip': [4, 5], 'url': 'new_url.com'}]
                }
            }
        ]

        return this `{'ips': [1, 2, 3, 4, 5], 'url': ['url.com', 'new_url.com']}`.

        :param collection_name: name of the collection whose keys to set.
        :param keys: python dict with keys to get from parse.
        """
        if not ignore_validation:
            Validator.validate_collection_name(collection_name)
            Validator.validate_set_iocs_keys_input(keys)
        self._iocs_keys[collection_name] = keys

    def close_session(self):
        """
        Closes the polling session. Use this function after finish polling to avoid problems.
        """
        self._session.close()


class TIPoller(Poller):
    def __init__(self, username, api_key, api_url):
        # type: (str, str, str) -> None
        """
        :param username: Login for TI.
        :param api_key: API key, generated in TI.
        :param api_url: API url
        """
        super().__init__(username=username, api_key=api_key, api_url=api_url)

    def search_feed_by_id(self, collection_name, feed_id):
        # type: (str, str) -> Parser
        """
        Searches for feed with `feed_id` in collection with `collection_name`.

        :param collection_name: in what collection to search.
        :param feed_id: id of feed to search.
        :rtype: :class:`Parser`
        """
        Validator.validate_collection_name(collection_name)
        endpoint = f"{collection_name}/{feed_id}"
        chunk = self.send_request(endpoint=endpoint, params={})
        portion = Parser(
            chunk,
            self._keys.get(collection_name, []),
            self._iocs_keys.get(collection_name, []),
        )
        return portion

    def search_file_in_threats(self, collection_name, feed_id, file_id):
        # type: (str, str, str) -> bytes
        """
        Searches for file with `file_id` in collection with `collection_name` in feed with `feed_id`.

        .. warning:: `Collection_name` should be apt/threat or hi/threat.

        :param collection_name: in what collection to search.
        :param feed_id: id of feed with file to search.
        :param file_id: if of file to search.
        """
        Validator.validate_collection_name(collection_name)
        endpoint = f"{collection_name}/{feed_id}/file/{file_id}"
        binary_file = self.send_request(
            endpoint=endpoint, params={}, decode=False
        )
        return binary_file

    def execute_action_by_id(
        self,
        collection_name,
        feed_id,
        action,
        request_params=None,
        decode=True,
    ):
        # type: (str, str, str, Optional[Dict], Optional[bool]) -> List[Dict[str, Any]]
        """
        Executes `action` for feed with `feed_id` in collection `collection_name`.

        :param collection_name: in what collection to search.
        :param feed_id: id of feed to search.
        :param action: action to execute (part of REST resource after "action/")
        :param request_params: dict of params to send with this request (e.g.: {"url_id": "1342312"})
        :param decode: True to get data in json format, False to get raw content
        """
        Validator.validate_collection_name(collection_name)
        if action[0] == "/":
            action = action[1::]
        endpoint = f"{collection_name}/{feed_id}/action/{action}"
        response = self.send_request(
            endpoint=endpoint, params=request_params, decode=decode
        )
        return response

    def global_search(self, query):
        # type: (str) -> List[Dict[str, Any]]
        """
        Global search across all collections with provided `query`, returns dict
        with information about collection, count, etc.

        :param query: query to search for.
        """
        endpoint = "search"
        response = self.send_request(endpoint=endpoint, params={"q": query})
        return response

    def graph_ip_search(self, query):
        # type: (str) -> List[Dict[str, Any]]
        """
        Graph IP search returns WHOIS information from Graph API

        :param query: query to search for.
        """

        endpoint = "utils/graph/ip"
        response = self.send_request(endpoint=endpoint, params={"ip": query})
        return response

    def graph_domain_search(self, query):
        # type: (str) -> List[Dict[str, Any]]
        """
        Graph domain search returns WHOIS information from Graph API

        :param query: query to search for.
        """

        endpoint = "utils/graph/domain"
        response = self.send_request(
            endpoint=endpoint, params={"domain": query}
        )
        return response

    def get_seq_update_dict(
        self,
        date=None,
        collection_name=None,
        apply_hunting_rules=None,
    ):
        # type: (Optional[str], Optional[str], Union[int, str]) -> Dict[str, int]
        """
        Gets dict with `seqUpdate` for all collections from server for provided date.
        If date is not provide returns dict for today.

        .. warning:: Date should be in "YYYY-MM-DD" format.

        :param date: defines for what date to get seqUpdate.
        :param apply_hunting_rules: apply or not client hunting rules to get only filtered data (applicable for public_leak, phishing_group and breached)
        :return: dict with collection names in keys and seq updates in values.
        """
        if date:
            Validator.validate_date_format(date=date, formats=["%Y-%m-%d"])

        endpoint = "sequence_list"
        if collection_name:
            Validator.validate_collection_name(collection_name=collection_name)
            params = {
                "date": date,
                "collection": collection_name,
                "apply_hunting_rules": apply_hunting_rules,
            }
        else:
            params = {"date": date, "apply_hunting_rules": apply_hunting_rules}
        buffer_dict = self.send_request(endpoint=endpoint, params=params).get(
            "list"
        )
        seq_update_dict = {}
        for key in CollectionConsts.TI_COLLECTIONS_INFO.keys():
            if key in buffer_dict.keys():
                seq_update_dict[key] = buffer_dict[key]
        return seq_update_dict

    def get_available_collections(self):
        """
        Returns list of available collections.
        """

        endpoint = "user/granted_collections"
        list_collection = ParserHelper.find_element_by_key(
            self.send_request(endpoint=endpoint, params={}), "collection"
        )
        available_collection = []
        for collection in CollectionConsts.TI_COLLECTIONS_INFO.keys():
            if collection in list_collection:
                available_collection.append(collection)
        for collection in CollectionConsts.ONLY_SEARCH_COLLECTIONS:
            if collection in list_collection:
                available_collection.append(collection)

        return available_collection

    def get_hunting_rules_collections(self):
        """
        Returns list of collections with hunting rules.
        """
        endpoint = "user/granted_collections"
        response = self.send_request(endpoint=endpoint, params={})
        filtered_collections = []
        for item in response:
            if item.get("huntingRulesUsed"):
                collection_name = item.get("collection")
                if (
                    collection_name
                    in CollectionConsts.TI_COLLECTIONS_INFO.keys()
                    or collection_name
                    in CollectionConsts.ONLY_SEARCH_COLLECTIONS
                ):
                    filtered_collections.append(collection_name)
        return filtered_collections

    def create_update_generator(
        self,
        collection_name,
        date_from=None,
        date_to=None,
        query=None,
        sequpdate=None,
        limit=None,
        apply_hunting_rules=None,
        is_tailored=None,
        apply_has_exploit=None,
        ignore_validation=None,
        parse_events=False,
        probable_corporate_access=None,
        unique=None,
        combolist=None,
    ):

        # type: (str, Optional[str], Optional[str], Optional[str], Union[int, str], Union[int, str], Union[int, str], Union[int, str], Union[int, str], Optional[bool], Optional[bool]) -> Generator[Parser, Any, None]
        session_type = "update"
        generator_info = TIGeneratorInfo(
            collection_name=collection_name,
            session_type=session_type,
            date_from=date_from,
            date_to=date_to,
            query=query,
            limit=limit,
            apply_hunting_rules=apply_hunting_rules,
            is_tailored=is_tailored,
            apply_has_exploit=apply_has_exploit,
            keys=self._keys.get(collection_name),
            iocs_keys=self._iocs_keys.get(collection_name),
            ignore_validation=ignore_validation,
            parse_events=parse_events,
            probable_corporate_access=probable_corporate_access,
            unique=unique,
            combolist=combolist,
        )
        generator_class = TIUpdateFeedGenerator(
            self, generator_info, sequpdate=sequpdate
        )
        return generator_class.create_generator()

    def create_search_generator(
        self,
        collection_name,
        date_from=None,
        date_to=None,
        query=None,
        limit=None,
        apply_hunting_rules=None,
        ignore_validation=None,
        parse_events=False,
    ):
        # type: (str, Optional[str], Optional[str], Optional[str], Union[int, str], Union[int, str], Optional[bool], Optional[bool]) -> Generator

        """
        Creates generator of :class:`Parser` class objects for the search session
        (feeds are sorted in descending order, **excluding compromised/breached amd compromised/reaper**)
        for `collection_name` with set parameters.

        .. warning:: Dates should be in one of this formats: "YYYY-MM-DD", "YYYY-MM-DDThh:mm:ssZ".
        For most collections, limits are set on the server and can't be exceeded.

        :param collection_name: collection to search.
        :param date_from: start date of search session.
        :param date_to: end date of search session.
        :param query: query to search during session.
        :param limit: size of portion in iteration.
        :param apply_hunting_rules: apply or not client hunting rules to get only filtered data (applicable for public_leak, phishing_group and breached)
        :rtype: Generator[:class:`Parser`]
        """
        session_type = "search"
        generator_info = TIGeneratorInfo(
            collection_name=collection_name,
            session_type=session_type,
            date_from=date_from,
            date_to=date_to,
            query=query,
            limit=limit,
            apply_hunting_rules=apply_hunting_rules,
            keys=self._keys.get(collection_name),
            iocs_keys=self._iocs_keys.get(collection_name),
            ignore_validation=ignore_validation,
            parse_events=parse_events,
        )
        generator_class = TISearchFeedGenerator(self, generator_info)
        return generator_class.create_generator()


class DRPPoller(Poller):
    """
    Poller is used for requests to DRP API.
    """

    def __init__(self, username, api_key, api_url):
        # type: (str, str, str) -> None
        """
        :param username: Login.
        :param api_key: API key, generated in your DRP Portal profile.
        """
        super().__init__(username=username, api_key=api_key, api_url=api_url)

    def change_status(self, feed_id, status):
        # type: (str , Union['approve', 'reject']) -> None
        """
        Changes the approval status of a feed item if it meets the required conditions.

        This method first searches for a feed by its ID in the `violation` collection.
        If the feed's current status is `'detected'` and its approve state is `'under_review'`,
        it sends a request to update the approval status.

        Args:
            feed_id (str): The unique identifier of the feed item.
            status (str): The new approval status to set. Must be either `'approve'` or `'reject'`.

        Raises:
            AttributeError: If the feed cannot be updated because its status does not meet the required conditions.
        """

        response = self.search_feed_by_id(feed_id=feed_id)
        violation = response.raw_dict.get("violation", None)
        if violation:
            if (
                violation.get("status") == "detected"
                and violation.get("approveState") == "under_review"
            ):
                self._send_change_approve_request(
                    feed_id=feed_id, status=status
                )
            else:
                logger.exception(
                    AttributeError(
                        "Can not change the status of the selected issue"
                    )
                )

    def _send_change_approve_request(self, feed_id, status):
        # type: (str , Union['approve', 'reject']) -> None
        """
        Sends a request to update the approval status of a specific feed item.

        This method posts to the `violation/change-approve` endpoint with the provided
        feed ID and the new approval status.

        Args:
            feed_id (str): The unique identifier of the feed item to update.
            status (str): The new approval status to set. Must be either `'approve'` or `'reject'`.

        Returns:
            None
        """
        collection_name = "violation/change-approve"
        Validator.validate_collection_name(collection_name)
        approve_status = True if status == "approve" else False
        json_data = {
            "violationId": feed_id,
            "approve": approve_status,
        }
        # Note: You cannot replace data with json here, as in this case the data will not be recognized
        response = self.send_request(
            endpoint=collection_name,
            method="POST",
            data=json.dumps(json_data),
            headers={
                "Content-Type": "application/json",
                "accept": "application/json",
            },
        )

    def get_brands(
        self,
    ):
        # type: () -> list
        """
        Retrieves a list of brands from the service.

        This method sends a GET request to the `settings/brands` collection,
        validates the collection name, and parses the response to extract
        the list of brands.

        Returns:
            list of dict: A list of brand objects, for example:
            [
                {"name": "Example Brand 1", "id": "exampleid1223"},
                {"name": "Example Brand 2", "id": "exampleid321"},
                ...
            ]
        """
        collection_name = "settings/brands"
        Validator.validate_collection_name(collection_name)
        response = self.send_request(endpoint=collection_name, method="GET")
        brands = ParserHelper.find_element_by_key(response, "data.brands")
        return brands

    def get_subscriptions(
        self,
    ):
        # type: () -> list
        """
        Retrieves a list of subscriptions from the service.

        This method sends a GET request to the `settings/subscriptions` collection,
        validates the collection name, and parses the response to extract
        the list of subscription names.

        Returns:
            list of str: A list of subscription names, for example:
            ['scam', 'example', ...]
        """
        collection_name = "settings/subscriptions"
        Validator.validate_collection_name(collection_name)
        response = self.send_request(endpoint=collection_name, method="GET")
        subscriptions = ParserHelper.find_element_by_key(
            response, "data.subscriptions"
        )
        return subscriptions

    def search_feed_by_id(self, feed_id):
        # type: (str, str) -> Parser
        """
        Searches for feed with `feed_id` in violation collection.

        :param feed_id: id of feed to search.
        :rtype: :class:`Parser`
        """
        collection_name = "violation"
        Validator.validate_collection_name(collection_name)
        endpoint = f"{collection_name}/{feed_id}"
        chunk = self.send_request(endpoint=endpoint, params={})
        portion = Parser(
            chunk,
            self._keys.get(collection_name, []),
            self._iocs_keys.get(collection_name, []),
        )
        return portion

    def get_seq_update_dict(
        self,
        date=None,
        collection=None,
    ):
        # type: (Optional[str], Optional[str]) -> Any[str, int]
        """
        Gets dict with `seqUpdate` key for each collection from server based on provided date, collection name or
        hunting rules. If date is not provided, returns dict for the current day.

        .. warning:: Date should be in "YYYY-MM-DD" format.

        :param date: defines start date to get seqUpdate.
        :param collection: filter by collection name
        :param apply_hunting_rules: apply or not client hunting rules to get only filtered data (applicable for public_leak, phishing_group and breached)
        :return: dict with collection names in keys and seq updates in values.
        """
        if date:
            Validator.validate_date_format(date=date, formats=["%Y-%m-%d"])

        # timestamp = datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp()
        # fmt_str = r"%Y-%m-%dT%H:%M:%S.%f"

        # replaces the fromisoformat, not available in python 3.6
        fmt_str = r"%Y-%m-%d"
        timestamp = (
            datetime.strptime(date, fmt_str)
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )

        seconds = datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).timestamp()
        miliseconds = seconds * 1000
        microseconds = miliseconds * 1000
        seqUpdate = int(microseconds)

        if collection:
            return seqUpdate
        else:
            seq_update_dict = {}
            for key in CollectionConsts.DRP_COLLECTIONS_INFO.keys():
                seq_update_dict[key] = seqUpdate
            return seq_update_dict

    def create_update_generator(
        self,
        collection_name,
        date_from=None,
        date_to=None,
        query=None,
        sequpdate=None,
        limit=None,
        subtypes=None,
        section=None,
        brands=None,
        ignore_validation=None,
        use_typo_squatting=None,
        approve_states=None,
    ):
        # type: (str, Optional[str], Optional[str], Optional[str], Union[int, str], Union[int, str], Union[List[int], List[str]], Union[List[int], List[str]], Optional[bool], Optional[bool]) -> Generator[Parser, Any, None]
        """
        Creates generator of :class:`Parser` class objects for an update session
        (feeds are sorted in ascending order) for `collection_name` with set parameters.
        `sequpdate` allows you to receive all relevant feeds. Such a request uses the sequpdate parameter,
        you will receive a portion of feeds that starts with the next `sequpdate` parameter for the current collection.
        For all feeds in the Group IB Intelligence continuous numbering is carried out.
        For example, the `sequpdate` equal to 1999998 can be in the `compromised/accounts` collection,
        and a feed with sequpdate equal to 1999999 can be in the `attacks/ddos` collection.
        If item updates (for example, if new attacks were associated with existing APT by our specialists or tor node
        has been detected as active again), the item gets a new parameter and it automatically rises in the database
        and "becomes relevant" again.

        .. warning:: Dates should be in one of this formats: "YYYY-MM-DD", "YYYY-MM-DDThh:mm:ssZ".
        For most collections, limits are set on the server and can't be exceeded.

        :param subtypes: ids int[]; 1 - counterfeit; 2 - piracy; 3 - partner_policy_compliance; 4 - trademark; 5 - malware; 6 - phishing; 7 - fraud; 8 - no_violation
        :param section: 1 - Web; 2 - Mobile apps; 3 - Marketplace; 4 - Social networks; 5 - Advertising; 6 - Instant messengers
        :param collection_name: collection to update.
        :param date_from: start date of update session.
        :param date_to: end date of update session.
        :param query: query to search during update session.
        :param sequpdate: identification number from which to start the session.
        :param limit: size of portion in iteration.
        :param apply_hunting_rules: apply or not client hunting rules to get only filtered data (applicable for public_leak, phishing_group and breached)
        :param use_typo_squatting: Whether to use typo-squatting detection.
        :rtype: Generator[:class:`Parser`]
        """

        # If none of the parameters are specified, but use_typo_squatting is set - set sequpdate to 1 to work correctly with use_typo_squatting
        if (
            date_from is None
            and date_to is None
            and sequpdate is None
            and use_typo_squatting
        ):
            sequpdate = 1

        session_type = "update"
        generator_info = DRPGeneratorInfo(
            collection_name=collection_name,
            session_type=session_type,
            date_from=date_from,
            date_to=date_to,
            query=query,
            limit=limit,
            keys=self._keys.get(collection_name),
            iocs_keys=self._iocs_keys.get(collection_name),
            subtypes=subtypes,
            section=section,
            brands=brands,
            approve_states=approve_states,
            ignore_validation=ignore_validation,
            use_typo_squatting=use_typo_squatting,
        )
        generator_class = DRPUpdateFeedGenerator(
            self, generator_info, sequpdate=sequpdate
        )
        return generator_class.create_generator()


class FeedGenerator(object):
    """
    Base Feed Generator class
    """

    def __init__(self, poller_object, generator_info):
        # type: (Union[TIPoller,  DRPPoller], Union[TIGeneratorInfo, DRPGeneratorInfo]) -> None
        self.i = 0
        self.total_amount = 0
        self.poller_object = poller_object
        self.generator_info = generator_info
        self.endpoint = self.generator_info.collection_name

    def _get_params(self):
        return {
            "df": self.generator_info.date_from,
            "dt": self.generator_info.date_to,
            "q": self.generator_info.query,
            "limit": self.generator_info.limit,
        }

    def _reset_params(self, portion):
        pass

    def create_generator(self):
        # type: () -> Generator[Parser, Any, None]
        logger.info(
            f"Starting {self.generator_info.session_type} "
            f"session for {self.generator_info.collection_name} collection"
        )

        while True:
            self.i += 1
            logger.info(f"Loading {self.i} portion")
            chunk = self.poller_object.send_request(
                endpoint=self.endpoint, params=self._get_params()
            )
            portion = Parser(
                chunk, self.generator_info.keys, self.generator_info.iocs_keys
            )
            logger.info(f"{self.i} portion was loaded")
            if portion.portion_size == 0:
                logger.info(
                    f"{self.generator_info.session_type} session for {self.generator_info.collection_name} "
                    f"collection was finished, loaded {self.total_amount} feeds"
                )
                break
            self.total_amount += portion.portion_size
            self._reset_params(portion)
            yield portion


class TIUpdateFeedGenerator(FeedGenerator):
    def __init__(self, poller_object, generator_info, sequpdate):
        # type: (Union[TIPoller], Union[TIGeneratorInfo], Union[int, str]) -> None
        super().__init__(poller_object, generator_info)
        self.sequpdate = sequpdate
        self.endpoint = f"{self.generator_info.collection_name}/updated"

    def create_generator(self):
        # type: () -> Generator[Parser, Any, None]
        logger.info(
            f"Starting {self.generator_info.session_type} "
            f"session for {self.generator_info.collection_name} collection"
        )

        while True:
            self.i += 1
            logger.info(f"Loading {self.i} portion")
            chunk = self.poller_object.send_request(
                endpoint=self.endpoint, params=self._get_params()
            )
            if (
                self.generator_info.parse_events
                and Validator.validate_group_collections(
                    self.generator_info.collection_name
                )
            ):
                expanded_data = {}
                expanded_data["count"] = chunk.get("count")
                expanded_data["seqUpdate"] = chunk.get("seqUpdate")
                expanded_data["items"] = []

                for item in chunk["items"]:
                    events = item.get("events", [])
                    if events:
                        for event in events:
                            expanded_event = dict(item)
                            expanded_event["events"] = [event]
                            expanded_data["items"].append(expanded_event)
                    else:
                        expanded_data["items"].append(item)
                chunk = expanded_data
            portion = Parser(
                chunk, self.generator_info.keys, self.generator_info.iocs_keys
            )
            logger.info(f"{self.i} portion was loaded")
            if portion.portion_size == 0:
                logger.info(
                    f"{self.generator_info.session_type} session for {self.generator_info.collection_name} "
                    f"collection was finished, loaded {self.total_amount} feeds"
                )
                break
            self.total_amount += portion.portion_size
            self._reset_params(portion)
            yield portion

    def _get_params(self):
        return {
            **super()._get_params(),
            "seqUpdate": self.sequpdate,
            "apply_hunting_rules": self.generator_info.apply_hunting_rules,
            "is_tailored": self.generator_info.is_tailored,
            "apply_has_exploit": self.generator_info.apply_has_exploit,
            "probable_corporate_access": self.generator_info.probable_corporate_access,  # Parameter for collection compromised/account_group
            "unique": self.generator_info.unique,  # Parameter for collection compromised/account_group
            "combolist": self.generator_info.combolist,  # Parameter for collection compromised/account_group
        }

    def _reset_params(self, portion):
        self.sequpdate = portion.sequpdate
        self.generator_info.date_from = None


class TISearchFeedGenerator(FeedGenerator):
    def __init__(self, poller_object, generator_info):
        # type: (Union[TIPoller], Union[TIGeneratorInfo]) -> None
        super().__init__(poller_object, generator_info)
        self.result_id = None

    def create_generator(self):
        # type: () -> Generator[Parser, Any, None]
        logger.info(
            f"Starting {self.generator_info.session_type} "
            f"session for {self.generator_info.collection_name} collection"
        )

        while True:
            self.i += 1
            logger.info(f"Loading {self.i} portion")
            chunk = self.poller_object.send_request(
                endpoint=self.endpoint, params=self._get_params()
            )
            if (
                self.generator_info.parse_events
                and Validator.validate_group_collections(
                    self.generator_info.collection_name
                )
            ):
                expanded_data = {}
                expanded_data["count"] = chunk.get("count")
                expanded_data["resultId"] = chunk.get("resultId")
                expanded_data["items"] = []

                for item in chunk["items"]:
                    events = item.get("events", [])
                    if events:
                        for event in events:
                            expanded_event = dict(item)
                            expanded_event["events"] = [event]
                            expanded_data["items"].append(expanded_event)
                    else:
                        expanded_data["items"].append(item)
                chunk = expanded_data
            portion = Parser(
                chunk, self.generator_info.keys, self.generator_info.iocs_keys
            )
            logger.info(f"{self.i} portion was loaded")
            if portion.portion_size == 0:
                logger.info(
                    f"{self.generator_info.session_type} session for {self.generator_info.collection_name} "
                    f"collection was finished, loaded {self.total_amount} feeds"
                )
                break
            self.total_amount += portion.portion_size
            self._reset_params(portion)
            yield portion

    def _get_params(self):
        return {**super()._get_params(), "resultId": self.result_id}

    def _reset_params(self, portion):
        self.result_id = portion._result_id
        (
            self.generator_info.date_from,
            self.generator_info.date_to,
            self.generator_info.query,
        ) = (None, None, None)


class DRPUpdateFeedGenerator(FeedGenerator):
    def __init__(self, poller_object, generator_info, sequpdate):
        # type: (Union[DRPPoller], Union[DRPGeneratorInfo], Union[int, str]) -> None
        super().__init__(poller_object, generator_info)
        self.sequpdate = sequpdate
        self.endpoint = f"{self.generator_info.collection_name}"

    def _get_params(self):
        params = {
            **super()._get_params(),
            "seqUpdate": self.sequpdate,
            "section": self.generator_info.section,
        }
        if self.generator_info.brands:
            params.update({"brandIds[]": self.generator_info.brands[0]})
        if self.generator_info.use_typo_squatting:
            params.update({"typoSquatting": "true"})
        if self.generator_info.approve_states:
            params.update(
                {"approveState[]": self.generator_info.approve_states[0]}
            )
        if self.generator_info.subtypes:
            params.update({"subtypes[]": self.generator_info.subtypes[0]})
        return params

    def _reset_params(self, portion):
        self.sequpdate = portion.sequpdate
        self.generator_info.date_from = None


class Parser(object):
    """
    An object that handles raw JSON with various methods.

    :param dict chunk: data portion.
    :param dict[str, str] keys: fields to find in portion.
    :param dict[str, str] iocs_keys: IOCs to find in portion.
    """

    def __init__(self, chunk, keys, iocs_keys):
        # type: (Dict, Dict[any, str], Dict[str, str]) -> None
        """
        :param chunk: data portion.
        :param keys: fields to find in portion.
        :param iocs_keys: IOCs to find in portion.
        """
        self.raw_dict = chunk
        self.raw_json = json.dumps(chunk)
        self.iocs_keys = iocs_keys
        self.keys = keys
        self.count = self.raw_dict.get(
            "count", self.raw_dict.get("total", None)
        )
        self.portion_size = len(self._return_items_list())
        self.sequpdate = self.raw_dict.get("seqUpdate", None)
        self._result_id = self.raw_dict.get("resultId", None)

    def _return_items_list(self):
        if self.count is not None:
            raw_dict = self.raw_dict.get("items", {})
        else:
            raw_dict = [self.raw_dict]
        return raw_dict

    def _keys_exist(self, feed, keys_road):
        # type: (Dict, List[str]) -> bool

        for k in keys_road:
            feed = feed.get(k, {})

        if feed:
            return True
        return False

    def _keys_found(self, feed, keys_road, check_list):
        # type: (Dict, List[str], List[str]) -> bool

        for k in keys_road:
            feed = feed.get(k, {})

        if isinstance(feed, list):
            raise ValueError("Value to check should be String not List.")

        if check_list:
            if feed in check_list:
                return True
        return False

    def parse_portion(
        self,
        keys=None,
        as_json=False,
        filter_map=None,
        ignore=False,
        check_existence=False,
        use_alternative_parser=False,
        **kwargs,
    ):
        # type: (Optional[Dict[any, str]], Optional[bool], Tuple[str, List], bool, bool, Any) -> Union[str, List[Dict[Any, Any]]]
        """
        Returns parsed portion list of feeds using keys provided for current collection.
        Every dict in list is single parsed feed.

        :param keys: if provided override base keys set in poller.
        :param as_json: if True returns portion in JSON format.
        :param filter_map: filter to **ignore**/**accept only** feeds which contains values in filter_map.
        Depends on **ignore** flag.
        :param ignore: flag to ignore values in filter_map. By default, set to False.
        :param check_existence: flag to check existence of a key in filter_map. By default, set to False.
        """

        if not self.keys and not keys:
            raise ParserException(
                "You didn't provide any keys for parsing portion."
            )
        if keys:
            Validator.validate_set_keys_input(keys)
        parsed_portion = []
        raw_dict = self._return_items_list()
        for feed in raw_dict:

            scip_flag = False

            # Filter logic, which depends on args: filter_map, ignore and check_existence
            if filter_map:
                for _filter in filter_map:

                    _keys_road = _filter[0].split(".")
                    _check_list = _filter[1]

                    if ignore:
                        # if ignore flag is True -> ignore keys from check_list
                        if self._keys_found(
                            feed=feed,
                            keys_road=_keys_road,
                            check_list=_check_list,
                        ):
                            scip_flag = True
                            continue
                    elif check_existence:
                        # if check_existence flag is True -> accept only if key_road not null
                        if not self._keys_exist(
                            feed=feed, keys_road=_keys_road
                        ):
                            scip_flag = True
                            continue
                    else:
                        # if ignore flag is False -> accept only keys from check_list
                        if not self._keys_found(
                            feed=feed,
                            keys_road=_keys_road,
                            check_list=_check_list,
                        ):
                            scip_flag = True
                            continue

                # scip feed if keys
                if scip_flag:
                    continue
            
            if use_alternative_parser:
                parser_helper = AlternativeParserHelper
            else:
                parser_helper = ParserHelper
            parsed_dict = parser_helper.find_by_template(
                feed, keys if keys else self.keys, **kwargs
            )
            parsed_portion.append(parsed_dict)

        if as_json:
            return json.dumps(parsed_portion)
        return parsed_portion

    def bulk_parse_portion(self, keys_list, as_json=False):
        # type: (List[Dict[any, str]], Optional[bool]) -> Union[str, List[List[Dict[Any, Any]]]]
        """
        Parses feeds in portion using every keys dict in the list.
        Every feed in parsed portion will be presented as list with parsed dicts for every keys dict.

        :param keys_list: list of keys dicts you want in return.
        :param as_json: if True returns portion in JSON format.
        """
        parsed_portion = []
        for keys in keys_list:
            parsed_portion.append(self.parse_portion(keys=keys))
        parsed_portion = [list(a) for a in zip(*parsed_portion)]

        if as_json:
            return json.dumps(parsed_portion)
        return parsed_portion

    def get_iocs(
        self,
        keys=None,
        as_json=False,
        filter_map=None,
        ignore=False,
        check_existence=False,
    ):
        # type: (Optional[Dict], Optional[bool], Tuple[str, List], bool, bool) -> Union[str, Dict[str, List]]
        """
        Returns parsed portion dict of feeds using ioc_keys provided for current collection.
        Keys are fields to search for current collection, values are list of gathered IOCs for current portion.

        :param keys: if provided override base iocs_keys set in poller.
        :param as_json: if True returns IOCs in JSON format.
        :param filter_map: filter to **ignore**/**accept only** feeds which contains values in filter_map. Depends on **ignore** flag.
        :param ignore: flag to ignore values in filter_map. By default, set to False.
        :param check_existence: flag to check existence of a key in filter_map. By default, set to False.
        """
        if not self.iocs_keys and not keys:
            raise ParserException(
                "You didn't provide any keys for getting IOCs."
            )
        if keys:
            Validator.validate_set_iocs_keys_input(keys)
            iocs_keys = keys
        else:
            iocs_keys = self.iocs_keys
        iocs_dict = {}
        raw_dict = self._return_items_list()
        for key, value in iocs_keys.items():
            iocs = []
            for feed in raw_dict:

                scip_flag = False

                # Filter logic, which depends on args: filter_map, ignore and check_existence
                if filter_map:
                    for _filter in filter_map:

                        _keys_road = _filter[0].split(".")
                        _check_list = _filter[1]

                        if ignore:
                            # if ignore flag is True -> ignore keys from check_list
                            if self._keys_found(
                                feed=feed,
                                keys_road=_keys_road,
                                check_list=_check_list,
                            ):
                                scip_flag = True
                                continue
                        elif check_existence:
                            # if check_existence flag is True -> accept only if key_road not null
                            if not self._keys_exist(
                                feed=feed, keys_road=_keys_road
                            ):
                                scip_flag = True
                                continue
                        else:
                            # if ignore flag is False -> accept only keys from check_list
                            if not self._keys_found(
                                feed=feed,
                                keys_road=_keys_road,
                                check_list=_check_list,
                            ):
                                scip_flag = True
                                continue

                    # scip feed if keys
                    if scip_flag:
                        continue

                ioc = ParserHelper.find_element_by_key(obj=feed, key=value)
                iocs.extend(ParserHelper.unpack_iocs(ioc))

            iocs_dict[key] = iocs

        if as_json:
            return json.dumps(iocs_dict)
        return iocs_dict
