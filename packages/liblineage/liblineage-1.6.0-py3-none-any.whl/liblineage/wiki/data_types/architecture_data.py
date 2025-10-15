#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, Union

from liblineage.wiki.data_types.base_data import BaseData

class ArchitectureData(BaseData):
	"""LineageOS architecture information.

	Attributes:
	- cpu: CPU architecture
	- userspace: Userspace architecture
	"""
	def __init__(
		self,
		cpu: str,
		userspace: str,
	):
		"""Initialize the architecture information."""
		super().__init__()

		self.cpu = cpu
		self.userspace = userspace

	@classmethod
	def from_data(cls, data: Union[str, Dict]) -> Union[str, "ArchitectureData"]:
		"""Create a architecture information object from YAML data."""
		if isinstance(data, str):
			architecture = data
		elif isinstance(data, dict):
			architecture = cls.from_dict(data)
		else:
			raise Exception("Invalid architecture data")

		return architecture
