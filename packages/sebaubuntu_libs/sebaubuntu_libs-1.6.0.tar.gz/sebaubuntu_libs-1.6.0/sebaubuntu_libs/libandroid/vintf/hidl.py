#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from typing import List, Optional, Set
from sebaubuntu_libs.libstring import removeprefix
from textwrap import indent
from xml.etree.ElementTree import Element

from sebaubuntu_libs.libandroid.vintf import INDENTATION
from sebaubuntu_libs.libandroid.vintf.common import Hal, cast_to_str_key

class HidlInterface:
	"""Class representing a HIDL interface."""
	def __init__(self, name: str, version: str, instance: str):
		"""Initialize an object."""
		self.name = name
		self.version = version
		self.instance = instance

	def __str__(self) -> str:
		return f"@{self.version}::{self.name}/{self.instance}"

	def __eq__(self, __o: object) -> bool:
		if isinstance(__o, HidlInterface):
			return (self.name == __o.name
			        and self.version == __o.version
			        and self.instance == __o.instance)
		return False

	def __hash__(self) -> int:
		return hash((self.name, self.version, self.instance))

	@classmethod
	def from_fqname(cls, fqname: str) -> 'HidlInterface':
		"""Create a AIDL HAL from a FQName."""
		temp = removeprefix(fqname, "@")
		version, temp = temp.split("::", 1)
		name, instance = temp.split("/", 1)

		return cls(name, version, instance)

	@classmethod
	def from_interface(cls, version: str, interface: Element) -> List['HidlInterface']:
		"""Create a AIDL HAL from an interface."""
		name = interface.findtext("name")
		assert name is not None, "Missing name in HIDL interface"

		return [
			HidlInterface(name, version, instance.text)
			for instance in interface.findall("instance")
		]

	@classmethod
	def from_interfaces(cls, version: str, interfaces: List[Element]) -> List['HidlInterface']:
		instances = [cls.from_interface(version, interface) for interface in interfaces]

		return [interface for interfaces in instances for interface in interfaces]

class HidlTransport:
	"""Class representing a HIDL transport type."""
	def __init__(self, name: str, passthrough_arch: Optional[str] = None):
		"""Initialize an object."""
		self.name = name
		self.passthrough_arch = passthrough_arch

	def __str__(self) -> str:
		if self.name == "passthrough":
			return f'<transport arch="{self.passthrough_arch}">{self.name}</transport>'

		return f'<transport>{self.name}</transport>'

	def __eq__(self, __o: object) -> bool:
		if isinstance(__o, HidlTransport):
			return (self.name == __o.name
			        and self.passthrough_arch == __o.passthrough_arch)
		return False
	
	def __hash__(self) -> int:
		return hash((self.name, self.passthrough_arch))

	@classmethod
	def from_element(cls, element: Element):
		"""Get a HidlTransport from an XML element."""
		name = element.text
		assert name is not None, "Missing name in HIDL transport"

		passthrough_arch = None
		if name == "passthrough":
			passthrough_arch = element.get("arch")

		return cls(name, passthrough_arch)

class HidlHal(Hal):
	"""Class representing a HIDL HAL."""
	def __init__(self, name: str, transport: HidlTransport, interfaces: Set[HidlInterface]):
		"""Initialize an object."""
		super().__init__(name)

		self.transport = transport
		self.interfaces = interfaces

	def __eq__(self, __o: object) -> bool:
		if isinstance(__o, HidlHal):
			return (self.name == __o.name
			        and self.transport == __o.transport
			        and self.interfaces == __o.interfaces)
		return False

	def __hash__(self) -> int:
		return hash((self.name, self.transport, self.interfaces))

	def __str__(self) -> str:
		string = f'<hal format="hidl">\n'
		string += indent(f'<name>{self.name}</name>\n', INDENTATION)
		string += indent(f'{self.transport}\n', INDENTATION)
		for interface in sorted(self.interfaces, key=cast_to_str_key):
			string += indent(f'<fqname>{interface}</fqname>\n', INDENTATION)
		string += '</hal>'

		return string

	@classmethod
	def from_entry(cls, entry: Element) -> 'HidlHal':
		"""Create a HIDL HAL from a VINTF entry."""
		assert entry.get("format") == "hidl"

		name = entry.findtext("name")
		transport = HidlTransport.from_element(entry.find("transport"))

		version = entry.findtext("version")

		interfaces = [
			HidlInterface.from_fqname(interface.text) for interface in entry.findall("fqname")
		]
		interface_elements = entry.findall("interface")
		if len(interface_elements) > 0:
			assert version is not None, "Missing version in HIDL HAL"
			interfaces.extend(HidlInterface.from_interfaces(version, interface_elements))

		interfaces = set(interfaces)

		return cls(name, transport, interfaces)
