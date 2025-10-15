#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from datetime import datetime
from typing import Any, Dict, List

from liblineage.updater.v2.build_file import BuildFile

class Build:
	"""LineageOS device build informations.

	Attributes:
	- date (str): The date of the build, in ISO 8601 format
	- datetime (datetime): The date of the build, as a date object
	- files (list[BuildFile]): List of files belonging to this build, first one being the OTA zip
	- os_patch_level (str): The OS patch level of the build in the format "YYYY-MM"
	- build_type (str): The type of the build (nightly, weekly, etc.)
	- version (str): The version of the build (e.g. 21.0)
	"""
	def __init__(
		self,
		date: str,
		datetime: datetime,
		files: List[BuildFile],
		os_patch_level: str,
		build_type: str,
		version: str,
	) -> None:
		self.date = date
		self.datetime = datetime
		self.files = files
		self.os_patch_level = os_patch_level
		self.build_type = build_type
		self.version = version

		self.ota_zip = self.files[0]

	@classmethod
	def from_json(cls, json: Dict[str, Any]):
		"""Create an object from a JSON object."""

		return cls(
			json["date"],
			datetime.fromtimestamp(json["datetime"]),
			[BuildFile.from_json(file) for file in json["files"]],
			json["os_patch_level"],
			json["type"],
			json["version"],
		)
