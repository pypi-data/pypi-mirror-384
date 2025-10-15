#
# Copyright (C) 2024 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional, Union

class NetworkData:
	"""LineageOS network information."""
	@classmethod
	def from_data(
		cls,
		data: Optional[Union[List, str]],
	) -> Optional[Union[List[str], Dict[str, List[str]]]]:
		"""Create a network information object from YAML data."""
		if data is None:
			networks = None
		elif isinstance(data, list):
			if data and isinstance(data[0], str):
				networks = data
			else:
				networks = {}
				for network_data in data:
					device, net = list(network_data.items())[0]
					networks[device] = net
		elif isinstance(data, str) and data == "None":
			networks = None
		else:
			raise Exception("Invalid network data")

		return networks
