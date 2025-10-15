#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from liblineage.hudson.build_target import BuildTarget
from liblineage.ota.full_update_info import FullUpdateInfo
from liblineage.wiki.device_data import DeviceData

class Device:
	"""Class representing a LineageOS supported device.

	Warning: This class is deprecated and will be removed in a future release."""
	def __init__(self, codename: str):
		"""Initialize the device."""
		self.codename = codename

	def get_device_data(self):
		return DeviceData.get_device_data(self.codename)

	def get_nightlies(self):
		return FullUpdateInfo.get_nightlies(self.codename)

	def get_hudson_build_target(self):
		return BuildTarget.get_device(self.codename)
