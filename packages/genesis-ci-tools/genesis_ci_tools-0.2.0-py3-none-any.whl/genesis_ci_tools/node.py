#    Copyright 2025 Genesis Corporation.
#
#    All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import annotations

import time
import typing as tp
import uuid as sys_uuid

import click
from bazooka import exceptions as bazooka_exc
from gcl_sdk.clients.http import base as http_client

from genesis_ci_tools import logger


def list_nodes(
    client: http_client.CollectionBaseClient,
    project_id: str | None,
) -> list[dict[str, tp.Any]]:
    params = {}
    if project_id is not None:
        params["project_id"] = project_id

    nodes = client.filter("/v1/nodes/", **params)
    return nodes


def add_node(
    client: http_client.CollectionBaseClient,
    uuid: sys_uuid.UUID | None,
    project_id: sys_uuid.UUID,
    cores: int,
    ram: int,
    root_disk: int,
    image: str,
    name: str,
    description: str,
    wait: bool,
) -> dict[str, tp.Any]:
    log = logger.ClickLogger()

    if uuid is None:
        uuid = sys_uuid.uuid4()

    data = {
        "uuid": str(uuid),
        "project_id": str(project_id),
        "cores": cores,
        "ram": ram,
        "root_disk_size": root_disk,
        "image": image,
        "name": name,
        "description": description,
    }

    # TODO(akremenetsky): Check the image exists

    try:
        node = client.create("/v1/nodes/", data=data)
    except bazooka_exc.ConflictError:
        raise click.ClickException(f"Node with UUID {uuid} already exists")

    if not wait:
        log.important(f"Node {uuid} created")
        return node

    while node["status"] != "ACTIVE":
        log.info(f"Waiting for node to be ready. Status: {node["status"]}")
        time.sleep(2)
        node = client.get("/v1/nodes/", uuid=uuid)

    return node


def add_or_update_node(
    client: http_client.CollectionBaseClient,
    uuid: sys_uuid.UUID | None,
    project_id: sys_uuid.UUID,
    cores: int,
    ram: int,
    root_disk: int,
    image: str,
    name: str,
    description: str,
    wait: bool,
) -> None:
    # If no UUID is provided, create a new node
    if uuid is None:
        return add_node(
            client,
            uuid,
            project_id,
            cores,
            ram,
            root_disk,
            image,
            name,
            description,
            wait,
        )

    # If UUID is provided, check if the node exists
    try:
        client.get("/v1/nodes/", uuid=uuid)
    except bazooka_exc.NotFoundError:
        return add_node(
            client,
            uuid,
            project_id,
            cores,
            ram,
            root_disk,
            image,
            name,
            description,
            wait,
        )

    # If the node exists, update it
    data = {
        "cores": cores,
        "ram": ram,
        "image": image,
        "name": name,
        "description": description,
    }

    return client.update("/v1/nodes/", uuid=uuid, **data)


def delete_node(
    client: http_client.CollectionBaseClient,
    uuid: sys_uuid.UUID | None,
) -> None:
    if uuid is None:
        raise click.UsageError("UUID must be provided")

    log = logger.ClickLogger()

    client.delete("/v1/nodes/", uuid=uuid)
    log.important(f"Deleted node {uuid}")
