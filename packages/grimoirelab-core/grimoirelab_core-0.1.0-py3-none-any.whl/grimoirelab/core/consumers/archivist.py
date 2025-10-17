# -*- coding: utf-8 -*-
#
# Copyright (C) GrimoireLab Contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

import json
import typing
import warnings

import certifi
import urllib3
import opensearchpy.exceptions

from opensearchpy import OpenSearch
from urllib3.util import create_urllib3_context

from .consumer import Consumer, Entry
from .consumer_pool import ConsumerPool

if typing.TYPE_CHECKING:
    from typing import Iterable


BULK_SIZE = 100
ROLLOVER_SIZE = "20gb"
DEFAULT_INDEX = "events"

MAPPING = {
    "mappings": {
        "properties": {
            "time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_second",
            },
            "data": {
                "properties": {
                    "message": {
                        "type": "text",
                        "index": True,
                    },
                    "AuthorDate": {
                        "type": "date",
                        "format": "EEE MMM d HH:mm:ss yyyy Z||EEE MMM d HH:mm:ss yyyy||strict_date_optional_time||epoch_millis",
                    },
                    "CommitDate": {
                        "type": "date",
                        "format": "EEE MMM d HH:mm:ss yyyy Z||EEE MMM d HH:mm:ss yyyy||strict_date_optional_time||epoch_millis",
                    },
                }
            },
        },
        "dynamic_templates": [
            {
                "notanalyzed": {
                    "match": "*",
                    "match_mapping_type": "string",
                    "mapping": {
                        "type": "keyword",
                    },
                }
            },
            {
                "formatdate": {
                    "match": "*",
                    "match_mapping_type": "date",
                    "mapping": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis",
                    },
                }
            },
        ],
    }
}


class OpenSearchArchivist(Consumer):
    """Store items in OpenSearch.

    This class implements the methods to store the events in an OpenSearch instance.

    :param url: OpenSearch URL
    :param user: OpenSearch username
    :param password: OpenSearch password
    :param index: OpenSearch index name
    :param bulk_size: Number of items to store in a single bulk request
    :param verify_certs: Whether to verify SSL certificates
    :param kwargs: Additional keyword arguments to pass to the parent class
    """

    def __init__(
        self,
        url: str,
        user: str | None = None,
        password: str | None = None,
        index: str = DEFAULT_INDEX,
        bulk_size: int = BULK_SIZE,
        verify_certs: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.index = index
        self.bulk_size = bulk_size
        self.client = create_opensearch_client(
            url=url,
            user=user,
            password=password,
            verify_certs=verify_certs,
        )

    def process_entries(self, entries: Iterable[Entry], recovery: bool = False) -> None:
        """Process entries and store them in the OpenSearch instance."""

        # This is to ensure the entry didn't fail because it was so big.
        if recovery:
            bulk_size = 1
        else:
            bulk_size = self.bulk_size

        bulk_json = ""
        entry_map = {}
        current = 0
        for entry in entries:
            event = entry.event
            data_json = json.dumps(event)
            bulk_json += '{{"index" : {{"_id" : "{}" }} }}\n'.format(event["id"])
            bulk_json += data_json + "\n"

            entry_map[event["id"]] = entry.message_id
            current += 1

            if current >= bulk_size:
                new_items, failed_ids = self._bulk(body=bulk_json, index=self.index)
                if new_items > 0:
                    # ACK successful items
                    for failed_id in failed_ids:
                        entry_map.pop(failed_id, None)
                    self.ack_entries(list(entry_map.values()))

                entry_map = {}
                current = 0
                bulk_json = ""

        if current > 0:
            new_items, failed_ids = self._bulk(body=bulk_json, index=self.index)
            if new_items > 0:
                # ACK successful items
                for failed_id in failed_ids:
                    entry_map.pop(failed_id, None)
                self.ack_entries(list(entry_map.values()))

    def _bulk(self, body: str, index: str) -> tuple[int, list]:
        """Store data in the OpenSearch instance.

        :param body: body of the bulk request
        :param index: index name
        :return number of items inserted, and ids of failed items
        """
        failed_ids = []
        error = None

        try:
            response = self.client.bulk(body=body, index=index)
        except Exception as e:
            self.logger.error(f"Failed to insert data to ES: {e}.")
            return 0, []

        if response["errors"]:
            for item in response["items"]:
                if "error" in item["index"]:
                    failed_ids.append(item["index"]["_id"])
                    error = str(item["index"]["error"])

            # Just print one error message
            self.logger.warning(f"Failed to insert data to ES: {error}.")

        num_inserted = len(response["items"]) - len(failed_ids)
        self.logger.info(f"{num_inserted} items uploaded to ES. {len(failed_ids)} failed.")

        return num_inserted, failed_ids


class OpenSearchArchivistPool(ConsumerPool):
    """Pool of OpenSearch archivist consumers."""

    CONSUMER_CLASS = OpenSearchArchivist

    def __init__(
        self,
        url: str,
        user: str | None = None,
        password: str | None = None,
        index: str = DEFAULT_INDEX,
        bulk_size: int = BULK_SIZE,
        rollover_indices: bool = True,
        rollover_size: str = ROLLOVER_SIZE,
        verify_certs: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.url = url
        self.user = user
        self.password = password
        self.index = index
        self.bulk_size = bulk_size
        self.rollover_indices = rollover_indices
        self.rollover_size = rollover_size
        self.verify_certs = verify_certs

    @property
    def extra_consumer_kwargs(self):
        kwargs = {
            "url": self.url,
            "user": self.user,
            "password": self.password,
            "bulk_size": self.bulk_size,
            "verify_certs": self.verify_certs,
        }
        if self.rollover_indices:
            kwargs["index"] = f"{self.index}-write"
        else:
            kwargs["index"] = self.index

        return kwargs

    def _setup_consumer_pool(self, burst: bool = False):
        """Configure OpenSearch before starting the workers."""

        client = create_opensearch_client(
            url=self.url,
            user=self.user,
            password=self.password,
            verify_certs=self.verify_certs,
        )
        if self.rollover_indices:
            self._configure_rollover_indices(client)
        else:
            self._create_index(client, index=self.index, body=MAPPING)

    def _configure_rollover_indices(self, client: OpenSearch):
        """Configure rollover indices in OpenSearch.

        The alias is the index name provided by the user.

        A rollover policy will be created to manage the rollover of indices
        based on the specified size. The index pattern for the policy will be
        `<alias>-*`, where `<alias>` is the provided index name.

        The first index will be created with the name `<alias>-000001` and will be
        associated with two aliases: `<alias>` (read alias) and `<alias>-write`
        (write alias).

        The read alias points to all indices associated with the alias, while the
        write alias points to the current index where new data will be written.
        When the current index reaches the specified size, a new index will be
        created and the write alias will be updated to point to the new index.
        This allows indexes to be rolled over without interrupting write operations.
        """
        alias_name = self.index
        alias_write_name = f"{alias_name}-write"
        policy_id = f"{alias_name}_rollover_policy"
        index_pattern = f"{alias_name}-*"

        self._create_rollover_policy(client, policy_id, index_pattern)
        self._create_rollover_index(client, alias_name, alias_write_name)

    def _create_rollover_policy(self, client: OpenSearch, policy_id: str, index_pattern: str):
        """Create rollover policy for the OpenSearch index."""

        rollover_policy = {
            "policy": {
                "policy_id": policy_id,
                "description": "Rollover index when it reaches a certain size",
                "default_state": "rollover",
                "states": [
                    {
                        "name": "rollover",
                        "actions": [
                            {
                                "retry": {"count": 3, "backoff": "exponential", "delay": "5m"},
                                "rollover": {"min_size": self.rollover_size, "copy_alias": True},
                            }
                        ],
                        "transitions": [],
                    }
                ],
                "ism_template": [
                    {
                        "index_patterns": [index_pattern],
                        "priority": 100,
                    }
                ],
            }
        }

        try:
            client.transport.perform_request(
                method="PUT",
                url=f"/_plugins/_ism/policies/{policy_id}",
                body=json.dumps(rollover_policy),
            )
            self.logger.info(f"Created rollover policy: {policy_id}")
        except opensearchpy.exceptions.ConflictError:
            self.logger.info(f"Rollover policy '{policy_id}' already exists.")
        except Exception as e:
            self.logger.error(f"Failed to create rollover policy: {e}")
            raise

    def _create_rollover_index(self, client: OpenSearch, alias_name: str, alias_write_name: str):
        """Create the initial rollover index and alias if they don't exist."""

        index_template = {
            "index_patterns": [f"{alias_name}-*"],
            "template": {
                "settings": {
                    "index.plugins.index_state_management.rollover_alias": alias_write_name
                },
                "mappings": MAPPING["mappings"],
            },
        }
        index_body = {"aliases": {alias_write_name: {"is_write_index": True}, alias_name: {}}}

        res = client.indices.put_index_template(
            name=f"{alias_name}_ism_rollover", body=index_template
        )
        if res and res.get("acknowledged", False):
            self.logger.info("Created index template for rollover indices.")

        self._create_index(client, index=f"{alias_name}-000001", body=index_body)

    def _create_index(self, client: OpenSearch, index, body=None):
        """Create the OpenSearch index with the specified body."""

        res = client.indices.create(index=index, body=body, ignore=400)
        if res and res.get("acknowledged", False):
            self.logger.info(f"Created index: {index}")
        else:
            if "resource_already_exists_exception" in res.get("error", {}).get("type", ""):
                self.logger.info(f"Index {index} already exists.")
            else:
                self.logger.error(
                    f"Failed to create index: {res.get('error', {}).get('reason', 'Unknown error')}"
                )
                raise opensearchpy.exceptions.ConnectionError()


def create_opensearch_client(
    url: str,
    user: str | None = None,
    password: str | None = None,
    verify_certs: bool = False,
) -> OpenSearch:
    """Create an OpenSearch client.

    Use the `certifi` package to handle SSL certificates and
    local system certificates if `verify_certs` is True.
    If `verify_certs` is False, ignore SSL warnings.

    :param url: OpenSearch URL
    :param user: OpenSearch username
    :param password: OpenSearch password
    :param verify_certs: Whether to verify SSL certificates
    :return: OpenSearch client instance
    """
    context = None

    if verify_certs:
        # Use certificates from the local system and certifi
        context = create_urllib3_context()
        context.load_default_certs()
        context.load_verify_locations(certifi.where())
    else:
        # Ignore SSL warnings if not verifying certificates
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        warnings.filterwarnings("ignore", message=".*verify_certs.*")

    auth = None
    if user and password:
        auth = (user, password)

    client = OpenSearch(
        hosts=[url],
        http_auth=auth,
        http_compress=True,
        verify_certs=verify_certs,
        ssl_context=context,
        ssl_show_warn=False,
        max_retries=3,
        retry_on_timeout=True,
    )

    return client
