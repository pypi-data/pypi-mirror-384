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

import abc
import typing as tp
import uuid as sys_uuid
import http as httplib
from urllib.parse import urljoin

import bazooka
from bazooka import exceptions as bazooka_exc
from restalchemy.dm import models


class AbstractAuthenticator(abc.ABC):

    @abc.abstractmethod
    def authenticate(self) -> None:
        """Authenticate the client."""

    @abc.abstractmethod
    def get_auth_header(self) -> dict[str, str]:
        """Get the authentication header."""


class CoreIamAuthenticator(AbstractAuthenticator):
    DEFAULT_CLIENT_UUID = sys_uuid.UUID("00000000-0000-0000-0000-000000000000")

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        client_id: str = "GenesisCoreClientId",
        client_secret: str = "GenesisCoreClientSecret",
        client_uuid: sys_uuid.UUID = DEFAULT_CLIENT_UUID,
        scope: str | None = None,
        ttl: int = 86400,  # 1 day
        http_client: bazooka.Client | None = None,
    ):
        self._http_client = http_client or bazooka.Client()

        client_uuid = str(client_uuid)
        self._url = (
            f"{base_url}/v1/iam/clients/{client_uuid}/actions/get_token/invoke"
        )

        self._headers = {"Content-Type": "application/x-www-form-urlencoded"}

        self._data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope or self.empty_scope(),
            "ttl": str(ttl),
        }

        self._access_token = None
        self._refresh_token = None

    def authenticate(self) -> None:
        response = self._http_client.post(
            self._url, headers=self._headers, data=self._data
        )
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]

    def get_auth_header(self) -> dict[str, str]:
        if not self._access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self._access_token}"}

    @classmethod
    def empty_scope(cls) -> str:
        return ""

    @classmethod
    def project_scope(cls, project_id: sys_uuid.UUID) -> str:
        return f"project:{project_id}"


class CollectionBaseClient:
    ACTIONS_KEY = "actions"
    INVOKE_KEY = "invoke"

    def __init__(
        self,
        base_url: str,
        http_client: bazooka.Client | None = None,
        auth: AbstractAuthenticator | None = None,
    ) -> None:
        self._http_client = http_client or bazooka.Client()
        self._base_url = base_url
        self._auth = auth

    def _collection_url(self, collection: str):
        if not self._base_url.endswith("/") and not collection.startswith("/"):
            return self._base_url + "/" + collection
        return self._base_url + collection

    def _request(
        self,
        method: httplib.HTTPMethod,
        url: str,
        data: dict[str : tp.Any] | None = None,
        json: dict[str : tp.Any] | None = None,
        params: dict[str : tp.Any] | None = None,
        headers: dict[str:str] | None = None,
    ):
        if method == httplib.HTTPMethod.POST:
            requester = self._http_client.post
        elif method == httplib.HTTPMethod.GET:
            requester = self._http_client.get
        elif method == httplib.HTTPMethod.PUT:
            requester = self._http_client.put
        elif method == httplib.HTTPMethod.DELETE:
            requester = self._http_client.delete
        else:
            raise ValueError(f"Method {method} is not supported")

        if self._auth is None:
            return requester(
                url, data=data, json=json, params=params, headers=headers
            )

        headers = headers or {}
        headers.update(self._auth.get_auth_header())

        try:
            return requester(
                url, data=data, json=json, params=params, headers=headers
            )
        except bazooka_exc.UnauthorizedError:
            # Perhaps we need to re-authenticate
            self._auth.authenticate()
            headers.update(self._auth.get_auth_header())
            return requester(
                url, data=data, json=json, params=params, headers=headers
            )

    def resource_url(self, collection: str, uuid: sys_uuid.UUID):
        return urljoin(self._collection_url(collection), str(uuid))

    def get(self, collection: str, uuid: sys_uuid.UUID) -> dict[str : tp.Any]:
        url = self.resource_url(collection, uuid)
        resp = self._request(httplib.HTTPMethod.GET, url)
        return resp.json()

    def filter(
        self, collection: str, **filters: tp.Dict[str, tp.Any]
    ) -> list[dict[str : tp.Any]]:
        resp = self._request(
            httplib.HTTPMethod.GET,
            self._collection_url(collection),
            params=filters,
        )
        return resp.json()

    def create(
        self, collection: str, data: dict[str : tp.Any]
    ) -> dict[str : tp.Any]:
        resp = self._request(
            httplib.HTTPMethod.POST,
            self._collection_url(collection),
            json=data,
        )
        return resp.json()

    def update(
        self,
        collection: str,
        uuid: sys_uuid.UUID,
        **params: tp.Dict[str, tp.Any],
    ) -> dict[str : tp.Any]:
        url = self.resource_url(collection, uuid)
        resp = self._request(httplib.HTTPMethod.PUT, url, json=params)
        return resp.json()

    def delete(self, collection: str, uuid: sys_uuid.UUID) -> None:
        url = self.resource_url(collection, uuid)
        self._request(httplib.HTTPMethod.DELETE, url)

    def do_action(
        self,
        collection: str,
        name: str,
        uuid: sys_uuid.UUID,
        invoke: bool = False,
        **kwargs,
    ) -> dict[str : tp.Any] | None:
        url = self.resource_url(collection, uuid) + "/"
        action_url = urljoin(urljoin(url, self.ACTIONS_KEY) + "/", name)

        if invoke:
            action_url = urljoin(action_url + "/", self.INVOKE_KEY)
            resp = self._request(
                httplib.HTTPMethod.POST, action_url, json=kwargs
            )
        else:
            resp = self._request(
                httplib.HTTPMethod.GET, action_url, params=kwargs
            )

        # Try to convert response to json
        resp.raise_for_status()
        try:
            return resp.json()
        except bazooka_exc.BaseHTTPException:
            return None


class CollectionBaseModelClient(CollectionBaseClient):
    __model__: tp.Type[models.SimpleViewMixin] = None
    __resource_client__: tp.Type["ResourceBaseModelClient"] = None
    __parent__: str | None = None

    def __init__(
        self,
        base_url: str,
        collection_path: str,
        http_client: bazooka.Client | None = None,
        auth: AbstractAuthenticator | None = None,
    ) -> None:
        super().__init__(base_url, http_client, auth)
        self._collection_path = collection_path

    def get_collection(self) -> str:
        return self._collection_path

    def __call__(
        self, resource_uuid: sys_uuid.UUID
    ) -> "ResourceBaseModelClient":
        if self.__resource_client__ is None:
            raise ValueError("Resource client is not defined")
        return self.__resource_client__(self, resource_uuid, self._http_client)

    def get(self, uuid: sys_uuid.UUID) -> models.SimpleViewMixin:
        return self.__model__.restore_from_simple_view(
            **super().get(self.get_collection(), uuid)
        )

    def filter(
        self, **filters: tp.Dict[str, tp.Any]
    ) -> list[models.SimpleViewMixin]:
        return [
            self.__model__.restore_from_simple_view(**o)
            for o in super().filter(self.get_collection(), **filters)
        ]

    def create(self, object: models.SimpleViewMixin) -> models.SimpleViewMixin:
        skip = tuple() if self.__parent__ is None else (self.__parent__,)
        data = object.dump_to_simple_view(skip=skip)
        return self.__model__.restore_from_simple_view(
            **super().create(self.get_collection(), data)
        )

    def update(
        self, uuid: sys_uuid.UUID, **params: tp.Dict[str, tp.Any]
    ) -> models.SimpleViewMixin:
        return self.__model__.restore_from_simple_view(
            **super().update(self.get_collection(), uuid, **params)
        )

    def delete(self, uuid: sys_uuid.UUID) -> None:
        super().delete(self.get_collection(), uuid)

    def do_action(
        self, name: str, uuid: sys_uuid.UUID, invoke: bool = False, **kwargs
    ) -> dict[str : tp.Any] | None:
        return super().do_action(
            self.get_collection(), name, uuid, invoke, **kwargs
        )


class StaticCollectionBaseModelClient(CollectionBaseModelClient):
    __collection_path__: str | None = None

    def __init__(
        self,
        base_url: str,
        http_client: bazooka.Client | None = None,
        auth: AbstractAuthenticator | None = None,
    ) -> None:
        super().__init__(base_url, self.__collection_path__, http_client, auth)


class ResourceBaseModelClient:
    ACTIONS_KEY = "actions"
    INVOKE_KEY = "invoke"

    __model__: tp.Type[models.SimpleViewMixin] = None

    def __init__(
        self,
        collection: StaticCollectionBaseModelClient,
        resource_uuid: sys_uuid.UUID,
        http_client: bazooka.Client | None = None,
    ):
        self._http_client = http_client or bazooka.Client()
        self._collection = collection
        self._resource_uuid = resource_uuid

    def resource_url(self):
        return self._collection.resource_url(
            self._collection.__collection_path__, self._resource_uuid
        )

    def get(self) -> models.SimpleViewMixin:
        url = self.resource_url()
        resp = self._http_client.get(url)
        return self.__model__.restore_from_simple_view(**resp.json())

    def update(self, **params: tp.Dict[str, tp.Any]) -> models.SimpleViewMixin:
        url = self.resource_url()
        resp = self._http_client.put(url, json=params)
        return self.__model__.restore_from_simple_view(**resp.json())

    def delete(self) -> None:
        url = self.resource_url()
        self._http_client.delete(url)

    def do_action(
        self, name: str, invoke: bool = False, **kwargs
    ) -> tp.Dict[str, tp.Any] | None:
        url = self.resource_url() + "/"
        action_url = urljoin(urljoin(url, self.ACTIONS_KEY) + "/", name)

        if invoke:
            action_url = urljoin(action_url + "/", self.INVOKE_KEY)
            resp = self._http_client.post(action_url, json=kwargs)
        else:
            resp = self._http_client.get(action_url, params=kwargs)

        # Try to convert response to json
        resp.raise_for_status()
        try:
            return resp.json()
        except bazooka_exc.BaseHTTPException:
            return None
