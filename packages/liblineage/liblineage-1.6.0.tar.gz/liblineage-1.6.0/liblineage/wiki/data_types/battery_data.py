#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional, Union

from liblineage.wiki.data_types.base_data import BaseData

class BatteryData(BaseData):
	"""LineageOS battery information.

	Attributes:
	- capacity: The battery capacity (mAh)
	- removable: Whether the battery is removable
	- tech: The battery technology
	"""
	def __init__(
		self,
		capacity: int,
		removable: bool,
		tech: Optional[str] = None,
	):
		"""Initialize the battery information."""
		super().__init__()

		self.capacity = capacity
		self.removable = removable
		self.tech = tech

	@classmethod
	def from_data(cls, data: Optional[Union[Dict, List, str]]) -> Optional[Union["BatteryData", Dict[str, "BatteryData"]]]:
		"""Create a battery information object from YAML data."""
		if data is None:
			battery = None
		elif isinstance(data, dict):
			battery = cls.from_dict(data)
		elif isinstance(data, list):
			battery = {}
			for bat in data:
				device, battery_data = list(bat.items())[0]
				battery[device] = cls.from_dict(battery_data)
		elif isinstance(data, str) and data == "None":
			battery = None
		else:
			raise Exception("Invalid battery data")

		return battery
