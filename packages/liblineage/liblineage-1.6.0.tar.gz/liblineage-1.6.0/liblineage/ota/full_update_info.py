#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from datetime import datetime
from typing import Dict

from liblineage.constants.versions import LINEAGEOS_TO_ANDROID_VERSION
from liblineage.updater.v1 import SyncV1Api
from liblineage.updater.v1.build import Build

class FullUpdateInfo:
	"""LineageOS full update information.

	Attributes:
	- datetime (datetime): The date and time of the update
	- filename (str): The filename of the update
	- id (str): The ID of the update
	- romtype (str): The ROM type of the update
	- size (int): The size of the update (bytes)
	- url (str): The URL of the update
	- version (str): The LineageOS version of the update (e.g. 18.1)

	Warning: This class is deprecated and will be removed in a future release.
	Please move to liblineage.updater.
	"""
	def __init__(
		self,
		datetime: datetime,
		filename: str,
		id: str,
		romtype: str,
		size: int,
		url: str,
		version: str,
	):
		"""Initialize the full update information."""
		self.datetime = datetime
		self.filename = filename
		self.id = id
		self.romtype = romtype
		self.size = size
		self.url = url
		self.version = version

		self.android_version = LINEAGEOS_TO_ANDROID_VERSION[version]

	@classmethod
	def from_json(cls, update: Dict):
		"""Create a full update information object from a JSON object.

		Warning: This class is deprecated and will be removed in a future release.
		Please move to liblineage.updater.
		"""
		return cls(
			datetime.fromtimestamp(update["datetime"]),
			update["filename"],
			update["id"],
			update["romtype"],
			update["size"],
			update["url"],
			update["version"]
		)

	@classmethod
	def from_V1_build(cls, build: Build):
		"""Create a full update information object from a V1 build object.

		Warning: This class is deprecated and will be removed in a future release.
		Please move to liblineage.updater."""
		return cls(
			build.datetime,
			build.filename,
			build.id,
			build.romtype,
			build.size,
			build.url,
			build.version
		)

	@classmethod
	def get_nightlies(cls, device: str):
		"""Get the latest OTAs for a device.

		Warning: This class is deprecated and will be removed in a future release.
		Please move to liblineage.updater."""
		builds = SyncV1Api.get_device_builds(device, "nightly", "1")

		return [cls.from_V1_build(build) for build in builds]
