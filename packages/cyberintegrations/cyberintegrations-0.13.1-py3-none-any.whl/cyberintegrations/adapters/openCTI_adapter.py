# -*- encoding: utf-8 -*-
"""
Copyright (c) 2025
"""
import time
import logging
from datetime import datetime, timedelta

from ..exception import (
    ConnectionException, ParserException, InputException,
    FileTypeError, EmptyCredsError, MissingKeyError,
    BadProtocolError, EmptyDataError
)
from ..cyberintegrations import TIPoller
from ..utils import Validator

logger = logging.getLogger(__name__)

class TIAdapter:
    """
    Adapter

    IOC - indicator of compromise (indicator of compromentation)

    Requires Config object with the next fields:

        PRODUCT_TYPE =
        PRODUCT_NAME =
        PRODUCT_VERSION =
        INTEGRATION =
        INTEGRATION_VERSION =
    """
    _poller: TIPoller | None = None
    

    def __init__(self, ti_creds_dict, proxies, config_obj, enabled_collections: list[str], collection_mapping_config: dict, collections_last_sequence_updates: dict, api_url=None):
        self._ti_creds_dict = ti_creds_dict
        self._proxies = proxies
        self.config = config_obj

        # self._poller = None
        self._api_url = api_url
        self._enabled_collections = enabled_collections
        self._mapping_config = collection_mapping_config # like JSON type 
        self._collections_last_sequence_updates = collections_last_sequence_updates

    def _set_up_poller(self):

        # Validate configs
        Validator.validate_keys_from_yaml(self._mapping_config)

        # Init mr poller
        if self._api_url:
            _mr_poller = TIPoller(
                username=self._ti_creds_dict.get('username'),
                api_key=self._ti_creds_dict.get('api_key'),
                api_url=self._api_url
            )
        else:
            _mr_poller = TIPoller(
                username=self._ti_creds_dict.get('username'),
                api_key=self._ti_creds_dict.get('api_key')
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
            integration_version=self.config.INTEGRATION_VERSION
        )

        return _mr_poller

    def _get_collection_date(self, collection: str):
        # Get collection default date
        _current_date = self.config.get_collection_settings(collection.replace('/', '_'), 'default_date')
        if not _current_date:
            _default_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            _current_date = _default_date

        return _current_date

    def _get_collection_seq_update(self, collection: str, current_date: str):
        # Get collection sequence update number
        _current_seq_update = None
        if self._collections_last_sequence_updates is not None and collection in self._collections_last_sequence_updates:
            _collection_state = self._collections_last_sequence_updates.get(collection)
            if isinstance(_collection_state, dict):
                _current_seq_update = _collection_state.get('sequpdate')
                
        # Get dict of seqUpdate for all collections
        if _current_seq_update is None:
            assert self._poller is not None
            _seq_update_dict = self._poller.get_seq_update_dict(date=current_date, collection_name=collection)
            _current_seq_update = _seq_update_dict.get(collection, None)

        return _current_seq_update

    def _set_poller(self):
        self._poller = self._set_up_poller()

    def _get_collection_generator_kwargs(self, collection: str) -> dict:
        """Build per-collection kwargs for TIPoller methods.

        Maps config values like use_hunting_rules -> apply_hunting_rules for TI collections.
        All params are optional; only non-None values will be passed further.
        """
        kwargs: dict = {}

        # normalize name for config accessor e.g. apt/threat -> apt_threat
        collection_key = collection.replace('/', '_')

        # Optional flags
        use_hunting_rules = self.config.get_collection_settings(collection_key, 'use_hunting_rules')
        parse_events = self.config.get_collection_settings(collection_key, 'parse_events')
        is_tailored = self.config.get_collection_settings(collection_key, 'is_tailored')
        apply_has_exploit = self.config.get_collection_settings(collection_key, 'apply_has_exploit')
        probable_corporate_access = self.config.get_collection_settings(collection_key, 'probable_corporate_access')
        unique = self.config.get_collection_settings(collection_key, 'unique')
        combolist = self.config.get_collection_settings(collection_key, 'combolist')

        # TI API expects apply_hunting_rules param name
        if use_hunting_rules is not None:
            kwargs['apply_hunting_rules'] = int(use_hunting_rules)
        if parse_events is not None:
            kwargs['parse_events'] = int(parse_events)
        if is_tailored is not None:
            kwargs['is_tailored'] = int(is_tailored)
        if apply_has_exploit is not None:
            kwargs['apply_has_exploit'] = int(apply_has_exploit)
        if probable_corporate_access is not None:
            kwargs['probable_corporate_access'] = int(probable_corporate_access)
        if unique is not None:
            kwargs['unique'] = int(unique)
        if combolist is not None:
            kwargs['combolist'] = int(combolist)

        return kwargs

    def _set_collection_keys(self, collection: str, keys: dict | None):
        # Set finder keys
        assert self._poller is not None
        self._poller.set_keys(
            collection_name=collection,
            keys=keys or {},
            ignore_validation=True
        )

    def _create_generator(self, collection, **kwargs):
        try:
            
            keys = self._mapping_config.get(collection, None)
            current_date = self._get_collection_date(collection)
            current_seq_update = self._get_collection_seq_update(collection, current_date)
            logger.info(f"Set keys for the collection {collection}, {self._mapping_config}")
            self._set_collection_keys(collection, keys)

            # Create Search Generator or Update Generator based on seqUpdate
            if current_seq_update is None:
                logger.info("{}  {}  {}".format(current_date, collection, current_seq_update))
                logger.exception("There is no data for last three days. Please increase {} default date!".format(
                    collection))
                logger.exception("Also check please access to this collections at Treat Intelligence!")
                return None
                # generator = self._poller.create_search_generator(
                #     collection_name=slashed_collection_name)
            else:
                logger.info("{}  {}  {}".format(current_date, collection, current_seq_update))

                # merge caller kwargs with per-collection kwargs
                per_collection_kwargs = self._get_collection_generator_kwargs(collection)
                merged_kwargs = {**kwargs, **per_collection_kwargs}

                generator = self._poller.create_update_generator(
                    collection_name=collection,
                    sequpdate=current_seq_update,
                    **merged_kwargs
                )
                
                prepared_data = {
                    collection: {"current_date":current_date}
                }

                return generator, prepared_data

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
                InputException
        ):
            logger.exception("Flaskyti error.")
            return None
        except Exception as e:
            logger.exception("Strange error: {0}".format(e))
            return None

    def create_generators(self, sleep_amount, **kwargs):
        self._set_poller()
        data = list()

        logger.info('──── GATHER INFO')
        try:
            for slashed_collection_name in self._enabled_collections:
                time.sleep(sleep_amount)
                result = self._create_generator(
                    slashed_collection_name,
                    **kwargs
                )
                if not result:
                    continue
                generator, prepared_data = result
                data.append(((
                    slashed_collection_name,
                    generator
                ), prepared_data))

        except Exception:
            logger.exception("Error while creating generators")
        finally:
            if self._poller:
                self._poller.close_session()

        logger.info('──── GENERATOR CREATED')
        return data

    def send_request(self, endpoint, params, decode=True, **kwargs):
        return self._poller.send_request(endpoint=endpoint, params=params, decode=decode, **kwargs)
