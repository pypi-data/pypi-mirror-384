#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Any, List

from liblineage.updater.v2.build import Build
from liblineage.updater.v2.device import Device
from liblineage.updater.v2.oem import Oem

def get_oems(json: List[Any]) -> List[Oem]:
	return [Oem.from_json(oem) for oem in json]

def get_device(json: Any) -> Device:
	return Device.from_json(json)

def get_device_builds(json: List[Any]) -> List[Build]:
	return [Build.from_json(build) for build in json]
