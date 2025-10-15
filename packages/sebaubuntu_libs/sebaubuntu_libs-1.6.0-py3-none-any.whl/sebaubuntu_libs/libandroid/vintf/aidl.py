#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from textwrap import indent
from typing import Set
from xml.etree.ElementTree import Element

from sebaubuntu_libs.libandroid.vintf import INDENTATION
from sebaubuntu_libs.libandroid.vintf.common import Hal, cast_to_str_key

class AidlInterface:
	"""Class representing a AIDL HAL."""
	def __init__(self, name: str, instance: str):
		"""Initialize an object."""
		self.name = name
		self.instance = instance

	def __str__(self) -> str:
		return f"{self.name}/{self.instance}"

	def __eq__(self, __o: object) -> bool:
		if isinstance(__o, AidlInterface):
			return (self.name == __o.name
			        and self.instance == __o.instance)
		return False

	def __hash__(self) -> int:
		return hash((self.name, self.instance))

	@classmethod
	def from_fqname(cls, string: str) -> 'AidlInterface':
		"""
		Create a AIDL HAL from a FQName.

		Example:
		ILights/default
		"""
		name, instance = string.split("/", 1)

		return cls(name, instance)

class AidlHal(Hal):
	"""Class representing a AIDL HAL."""
	def __init__(self, name: str, interfaces: Set[AidlInterface]):
		"""Initialize an object."""
		super().__init__(name)

		self.interfaces = interfaces

	def __str__(self) -> str:
		string = f'<hal format="aidl">\n'
		string += indent(f'<name>{self.name}</name>\n', INDENTATION)
		for interface in sorted(self.interfaces, key=cast_to_str_key):
			string += indent(f'<fqname>{interface}</fqname>\n', INDENTATION)
		string += '</hal>'

		return string

	@classmethod
	def from_entry(cls, entry: Element) -> 'AidlHal':
		"""Create a AIDL HAL from a VINTF entry."""
		assert entry.get("format") == "aidl"

		name = entry.findtext("name")
		assert name is not None, "Missing name in AIDL HAL"

		interfaces = set([AidlInterface.from_fqname(interface.text)
		                  for interface in entry.findall("fqname")])

		return cls(name, interfaces)
