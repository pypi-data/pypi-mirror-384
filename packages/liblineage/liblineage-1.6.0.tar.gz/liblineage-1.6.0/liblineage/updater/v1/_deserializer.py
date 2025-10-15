#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Any, Dict, List

from liblineage.updater.v1.build import Build

def get_device_builds(json: Dict[str, List[Any]]) -> List[Build]:
	return [Build.from_json(build) for build in json["response"]]

def get_device_types(json: Dict[str, List[Any]]) -> List[str]:
	return json["response"]

def get_devices(json: Dict[str, List[str]]) -> Dict[str, List[str]]:
	return json
