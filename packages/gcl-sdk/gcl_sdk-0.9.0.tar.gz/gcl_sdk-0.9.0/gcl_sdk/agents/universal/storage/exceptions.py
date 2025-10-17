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
from gcl_sdk.common import exceptions
from gcl_sdk.agents.universal.storage import base


class TargetFieldsStorageException(exceptions.UniversalAgentException):
    __template__ = "An unknown target fields storage exception occurred."


class ItemAlreadyExists(TargetFieldsStorageException):
    __template__ = "The item already exists: {item}"
    item: base.TargetFieldItem


class ItemNotFound(TargetFieldsStorageException):
    __template__ = "The item not found: {item}"
    item: base.TargetFieldItem
