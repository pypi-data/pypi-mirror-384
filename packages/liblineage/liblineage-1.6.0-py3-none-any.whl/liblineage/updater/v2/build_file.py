#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Any, Dict

class BuildFile:
	"""LineageOS device build files informations.

	Attributes:
	- filename (str): The filename of the file
	- filepath (str): The filepath of the file in the server
	- sha1 (str): The SHA1 hash of the file
	- sha256 (str): The SHA256 hash of the file
	- size (int): The size of the file, in bytes
	- url (str): The URL to download the file
	"""
	def __init__(
		self,
		filename: str,
		filepath: str,
		sha1: str,
		sha256: str,
		size: int,
		url: str,
	) -> None:
		self.filename = filename
		self.filepath = filepath
		self.sha1 = sha1
		self.sha256 = sha256
		self.size = size
		self.url = url

	@classmethod
	def from_json(cls, json: Dict[str, Any]):
		"""Create an object from a JSON object."""
		return cls(
			json["filename"],
			json["filepath"],
			json["sha1"],
			json["sha256"],
			json["size"],
			json["url"],
		)
