#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""LineageOS updater v1 API."""

from typing import Dict, List

from liblineage.updater import BASE_API_URL
from liblineage.updater.v1._deserializer import (
    get_device_builds,
	get_device_types,
	get_devices,
)
from liblineage.updater.v1.build import Build
from liblineage.updater.http_utils import AsyncHttpRequests, SyncHttpRequests

API_URL = f"{BASE_API_URL}/v1"

class AsyncV1Api:
	@staticmethod
	async def get_device_builds(device: str, rom_type: str, incremental_version: str) -> List[Build]:
		"""Get the list of builds for a device."""
		json = await AsyncHttpRequests.get_json(f"{API_URL}/{device}/{rom_type}/{incremental_version}")
		return get_device_builds(json)

	@staticmethod
	async def get_device_types(device: str) -> List[str]:
		"""Get the list of available build types for a device."""
		json = await AsyncHttpRequests.get_json(f"{API_URL}/types/{device}")
		return get_device_types(json)

	@staticmethod
	async def get_devices() -> Dict[str, List[str]]:
		"""Get the list of maintained devices, as a dictionary of version to list of devices."""
		json = await AsyncHttpRequests.get_json(f"{API_URL}/devices")
		return get_devices(json)

class SyncV1Api:
	@staticmethod
	def get_device_builds(device: str, rom_type: str, incremental_version: str) -> List[Build]:
		"""Get the list of builds for a device."""
		json = SyncHttpRequests.get_json(f"{API_URL}/{device}/{rom_type}/{incremental_version}")
		return get_device_builds(json)

	@staticmethod
	def get_device_types(device: str) -> List[str]:
		"""Get the list of available build types for a device."""
		json = SyncHttpRequests.get_json(f"{API_URL}/types/{device}")
		return get_device_types(json)

	@staticmethod
	def get_devices() -> Dict[str, List[str]]:
		"""Get the list of maintained devices, as a dictionary of version to list of devices."""
		json = SyncHttpRequests.get_json(f"{API_URL}/devices")
		return get_devices(json)
