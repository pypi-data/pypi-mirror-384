#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from datetime import datetime
from typing import Any, Dict

class Build:
	"""LineageOS device build informations.

	Attributes:
	- datetime (datetime): The date of the build, as a datetime object
	- filename (str): The filename of the update
	- id (str): The ID of the update
	- romtype (str): The update type (e.g. nightly)
	- size (int): The size of the file, in bytes
	- url (str): The URL to download the OTA zip
	- version (str): The LineageOS version of the update (e.g. 18.1)
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

	@classmethod
	def from_json(cls, update: Dict[str, Any]):
		"""Create an object from a JSON object."""
		return cls(
			datetime.fromtimestamp(update["datetime"]),
			update["filename"],
			update["id"],
			update["romtype"],
			update["size"],
			update["url"],
			update["version"]
		)
