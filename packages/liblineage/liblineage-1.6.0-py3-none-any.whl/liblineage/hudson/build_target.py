#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from datetime import date, timedelta
from random import Random
import requests

from liblineage.constants.infra import GITHUB_ORG
from liblineage.hudson.period import Period

LINEAGE_BUILD_TARGETS_FILE = f"https://raw.githubusercontent.com/{GITHUB_ORG}/hudson/main/lineage-build-targets"

class BuildTarget:
	def __init__(
		self,
		device: str,
		build_type: str,
		branch_name: str,
		period: Period,
	):
		self.device = device
		self.build_type = build_type
		self.branch_name = branch_name
		self.period = period

	def __str__(self) -> str:
		return f"{self.device} {self.build_type} {self.branch_name} {self.period}"

	@classmethod
	def from_api(cls, line: str):
		args = line.split()
		return cls(args[0], args[1], args[2], Period(args[3]))

	@classmethod
	def get_lineage_build_targets(cls):
		response = requests.get(url=LINEAGE_BUILD_TARGETS_FILE).text.split("\n")
		return [cls.from_api(line) for line in response if line and not line.startswith("#")]

	@classmethod
	def get_device(cls, device: str):
		"""Get the build target given a device codename."""
		# There can't be duplicates, plus this will miserably fail if this device isn't there
		return [target for target in cls.get_lineage_build_targets() if target.device == device][0]

	def get_next_build_date(self) -> date:
		"""Get the next build date for this build target."""
		today = date.today()

		if self.period == Period.NIGHTLY:
			return today + timedelta(days=1)

		random = Random(self.device)

		if self.period == Period.WEEKLY:
			day_of_week = random.randint(1, 7)
			delta_day = day_of_week - today.isoweekday()

			if delta_day <= 0:
				# Go to next week
				delta_day += 7

			return today + timedelta(days=delta_day)

		if self.period == Period.MONTHLY:
			day_of_month = random.randint(1, 28)
			delta_day = day_of_month - today.day

			if delta_day <= 0:
				# Go to next month
				month_to_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
				delta_day += month_to_days[today.month-1]

			return today + timedelta(days=delta_day)

		raise NotImplementedError(f"Unknown period {self.period}")
