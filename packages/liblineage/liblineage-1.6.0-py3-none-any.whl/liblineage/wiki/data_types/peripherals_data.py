#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional, Union

class PeripheralsData:
	"""LineageOS peripherals information."""
	@classmethod
	def from_data(cls, data: Optional[Union[List, str]]) -> Optional[Union[List[str], Dict[str, List[str]]]]:
		"""Create a peripherals information object from YAML data."""
		if data is None:
			peripherals = None
		elif isinstance(data, list):
			if data and isinstance(data[0], str):
				peripherals = data
			else:
				peripherals = {}
				for peripherals_data in data:
					device, periph = list(peripherals_data.items())[0]
					peripherals[device] = periph
		elif isinstance(data, str) and data == "None":
			peripherals = None
		else:
			raise Exception("Invalid peripherals data")

		return peripherals
