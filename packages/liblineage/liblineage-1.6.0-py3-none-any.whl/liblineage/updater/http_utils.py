#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

import aiohttp
import requests

class AsyncHttpRequests:
	@classmethod
	async def get_json(cls, url: str, **kwargs):
		async with aiohttp.ClientSession() as session:
			async with session.get(url, **kwargs) as resp:
				return await resp.json()

class SyncHttpRequests:
	@classmethod
	def get_json(cls, url: str, **kwargs):
		return requests.get(url, **kwargs).json()
