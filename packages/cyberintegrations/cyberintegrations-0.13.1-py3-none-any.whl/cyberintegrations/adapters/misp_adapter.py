# -*- encoding: utf-8 -*-
"""
Copyright (c) 2025
"""
import logging
import time
from datetime import datetime, timedelta

from ..cyberintegrations import TIPoller
from ..exception import (
    BadProtocolError,
    ConnectionException,
    EmptyCredsError,
    EmptyDataError,
    FileTypeError,
    InputException,
    MissingKeyError,
    ParserException,
)
from ..utils import ConfigParser, FileHandler, Validator

logger = logging.getLogger(__name__)


class GIBAdapter:
    """
    Group-IB Adapter

    IOC - indicator of compromise (indicator of compromentation)
    """

    _enabled_collections: list = None
    _endpoints_config: dict = None  # YAML
    _mapping_config: dict = None  # JSON

    _poller: TIPoller = None

    def __init__(self, gib_creds_dict, proxies, config_obj):
        # WARNING: At the moment, gib_creds_dict also contains api_url. In the future, it may be worth rewriting this.
        self._gib_creds_dict = gib_creds_dict
        self._proxies = proxies
        self.config = config_obj
        self._fh = FileHandler()
        self._cp = ConfigParser()

    def _set_up_poller(self):

        # Read configs before run
        self._endpoints_config = self._fh.read_yaml_config(
            config=self.config.CONFIG_YML
        )
        self._mapping_config = self._fh.read_json_config(
            config=self.config.CONFIG_JSON
        )

        # Validate configs
        Validator.validate_collections_from_yaml(self._endpoints_config)
        Validator.validate_keys_from_yaml(self._mapping_config)

        # Get enabled collections
        self._enabled_collections = self._cp.get_enabled_collections(
            self._endpoints_config
        )

        # Get GIB creds
        _gib_creds = self._cp.get_creds(self._gib_creds_dict)

        # Init mr poller
        _mr_poller = TIPoller(
            username=_gib_creds.USERNAME.value,
            api_key=_gib_creds.API_KEY.value,
            api_url=_gib_creds.API_URL.value,
        )

        # Add TLS certificate check and proxy settings
        _mr_poller.set_verify(True)
        if self._proxies:
            _mr_poller.set_proxies(**self._proxies)

        _mr_poller.set_product(
            product_type=self.config.PRODUCT_TYPE,
            product_name=self.config.PRODUCT_NAME,
            product_version=self.config.PRODUCT_VERSION,
            integration_name=self.config.INTEGRATION,
            integration_version=self.config.INTEGRATION_VERSION,
        )

        return _mr_poller

    def _get_collection_date(self, collection):
        # Get collection default date
        _current_date = (
            self._endpoints_config.get("collections")
            .get(collection)
            .get("default_date")
        )
        if not _current_date:
            _default_date = (datetime.now() - timedelta(days=3)).strftime(
                "%Y-%m-%d"
            )
            _current_date = _default_date

        return _current_date

    def _get_collection_seq_update(self, collection, current_date):
        # Get collection sequence update number
        _current_seq_update = (
            self._endpoints_config.get("collections")
            .get(collection)
            .get("seqUpdate", None)
        )

        # Get dict of seqUpdate for all collections
        if _current_seq_update is None:
            _seq_update_dict = self._poller.get_seq_update_dict(
                date=current_date, collection_name=collection
            )
            _current_seq_update = _seq_update_dict.get(collection, None)

        return _current_seq_update

    def _set_poller(self):
        self._poller = self._set_up_poller()

    def _set_collection_keys(self, collection, keys):
        # Set finder keys
        self._poller.set_keys(collection_name=collection, keys=keys)

    def _save_collection_info(self, collection, seq_update, date):
        # Save sequence update number and default date to config
        prepared_data = {"seqUpdate": seq_update, "default_date": date}

        self._fh.save_collection_info(
            config=self.config.CONFIG_YML,
            collection=collection,
            **prepared_data
        )

    def _create_generator(self, collection, **kwargs):
        try:
            keys = self._mapping_config.get(collection, None)
            current_date = self._get_collection_date(collection)
            current_seq_update = self._get_collection_seq_update(
                collection, current_date
            )

            self._set_collection_keys(collection, keys)

            # Create Search Generator or Update Generator based on seqUpdate
            if current_seq_update is None:
                logger.info(
                    "{}  {}  {}".format(
                        current_date, collection, current_seq_update
                    )
                )
                logger.exception(
                    "There is no data for last three days. Please increase {} default date!".format(
                        collection
                    )
                )
                logger.exception(
                    "Also check please access to this collections at GIB Treat Intelligence!"
                )
                return None
            else:
                logger.info(
                    "{}  {}  {}".format(
                        current_date, collection, current_seq_update
                    )
                )

                generator = self._poller.create_update_generator(
                    collection_name=collection,
                    sequpdate=current_seq_update,
                    **kwargs
                )

                self._save_collection_info(
                    collection, current_seq_update, current_date
                )

                return generator

        except InputException:
            logger.exception("Wrong input.")
            return None
        except ConnectionException:
            logger.exception("Connection error.")
            return None
        except ParserException:
            logger.exception("Parsing error.")
            return None
        except (
            FileTypeError,
            EmptyCredsError,
            MissingKeyError,
            BadProtocolError,
            EmptyDataError,
            InputException,
        ):
            logger.exception("Flaskyti error.")
            return None
        except Exception as e:
            logger.exception("Strange error: {0}".format(e))
            return None

    def create_generators(self, sleep_amount, **kwargs):
        self._set_poller()
        generator_list = list()

        logger.info("──── GATHER INFO")
        try:
            for slashed_collection_name in self._enabled_collections:
                time.sleep(sleep_amount)
                generator = self._create_generator(
                    slashed_collection_name, **kwargs
                )
                generator_list.append((slashed_collection_name, generator))

        except Exception:
            logger.exception("Error while creating generators")
        finally:
            if self._poller:
                self._poller.close_session()

        logger.info("──── GENERATOR CREATED")
        return generator_list

    def send_request(self, endpoint, params, decode=True, **kwargs):
        return self._poller.send_request(
            endpoint=endpoint, params=params, decode=decode, **kwargs
        )
