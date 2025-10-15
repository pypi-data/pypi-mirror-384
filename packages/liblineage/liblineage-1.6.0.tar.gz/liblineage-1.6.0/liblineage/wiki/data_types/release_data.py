#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from datetime import datetime, date
from typing import Dict, List, Union

class ReleaseData:
	"""LineageOS release information."""
	@staticmethod
	def convert_release_date(data: Union[int, str]):
		data = str(data)
		# YYYY-MM-DD
		try:
			return date.fromisoformat(data)
		except ValueError:
			# YYYY-MM
			try:
				return datetime.strptime(data, "%Y-%m").date()
			except ValueError:
				# YYYY
				return datetime.strptime(data, "%Y").date()

	@classmethod
	def from_data(cls, data: Union[date, int, str, List]) -> Union[date, Dict[str, date]]:
		"""Create a release information object from YAML data."""
		if isinstance(data, date):
			release = data
		elif isinstance(data, int):
			release = cls.convert_release_date(data)
		elif isinstance(data, str):
			release = cls.convert_release_date(data)
		elif isinstance(data, list):
			release = {}
			for release_data in data:
				device, rel = list(release_data.items())[0]
				release[device] = cls.convert_release_date(rel)
		else:
			raise Exception("Invalid release data")

		return release
