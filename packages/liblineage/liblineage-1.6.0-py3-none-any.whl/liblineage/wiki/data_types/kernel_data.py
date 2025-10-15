#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, Optional

from liblineage.constants.infra import GITHUB_ORG_URL
from liblineage.wiki.data_types.base_data import BaseData

class KernelData(BaseData):
	"""The format required for the kernel property.

	Attributes:
	- repo: Kernel repo
	- version: Kernel version
	"""
	def __init__(
		self,
		repo: str,
		version: float,
	):
		"""Initialize the kernel information."""
		super().__init__()

		self.repo = f"{GITHUB_ORG_URL}/{repo}"
		self.version = version

	@classmethod
	def from_data(cls, data: Optional[Dict]) -> Optional["KernelData"]:
		"""Create a kernel information object from YAML data."""
		if data is None:
			kernel = None
		elif isinstance(data, dict):
			kernel = cls.from_dict(data)
		else:
			raise Exception("Invalid kernel data")

		return kernel
