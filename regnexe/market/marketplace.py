from typing import Protocol, runtime_checkable

from regnexe.plugin.descriptor import CapabilityDescriptor, PluginDescriptor


@runtime_checkable
class Marketplace(Protocol):
    def install(self, plugin: PluginDescriptor) -> None: ...
    def search(self, query: str) -> list[CapabilityDescriptor]: ...
    def resolve(self, capability_id: str) -> CapabilityDescriptor: ...
