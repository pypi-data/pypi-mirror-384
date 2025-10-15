#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""LineageOS updater v2 API."""

from typing import List

from liblineage.updater import BASE_API_URL
from liblineage.updater.v2._deserializer import (
	get_oems,
	get_device,
	get_device_builds,
)
from liblineage.updater.v2.build import Build
from liblineage.updater.v2.device import Device
from liblineage.updater.v2.oem import Oem
from liblineage.updater.http_utils import AsyncHttpRequests, SyncHttpRequests

API_URL = f"{BASE_API_URL}/v2"

class AsyncV2Api:
	@staticmethod
	async def get_oems() -> List[Oem]:
		"""Get the list of OEMs."""
		json = await AsyncHttpRequests.get_json(f"{API_URL}/oems")
		return get_oems(json)

	@staticmethod
	async def get_device(device: str) -> Device:
		"""Get the device information."""
		json = await AsyncHttpRequests.get_json(f"{API_URL}/devices/{device}")
		return get_device(json)

	@staticmethod
	async def get_device_builds(device: str) -> List[Build]:
		"""Get the list of builds for a device."""
		json = await AsyncHttpRequests.get_json(f"{API_URL}/devices/{device}/builds")
		return get_device_builds(json)

class SyncV2Api:
	@staticmethod
	def get_oems() -> List[Oem]:
		"""Get the list of OEMs."""
		json = SyncHttpRequests.get_json(f"{API_URL}/oems")
		return get_oems(json)

	@staticmethod
	def get_device(device: str) -> Device:
		"""Get the device information."""
		json = SyncHttpRequests.get_json(f"{API_URL}/devices/{device}")
		return get_device(json)

	@staticmethod
	def get_device_builds(device: str) -> List[Build]:
		"""Get the list of builds for a device."""
		json = SyncHttpRequests.get_json(f"{API_URL}/devices/{device}/builds")
		return get_device_builds(json)
