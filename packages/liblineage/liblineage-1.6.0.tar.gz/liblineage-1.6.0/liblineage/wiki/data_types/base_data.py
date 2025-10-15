#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Any, Dict

class BaseData:
	"""Base class for data types."""

	@classmethod
	def from_data(cls, data: Any) -> Any:
		"""Create a data type object from YAML data."""
		raise NotImplementedError

	@classmethod
	def from_dict(cls, data: Dict):
		"""Create a data type object from a dictionary."""
		return cls(**data)

	def __str__(self) -> str:
		"""Return a string representation of the data type."""
		return ", ".join([f"{k}: {v}" for k, v in self.__dict__.items()])
