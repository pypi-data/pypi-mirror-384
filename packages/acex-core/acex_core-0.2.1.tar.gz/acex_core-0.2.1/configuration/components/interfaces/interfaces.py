
from acex.core.configuration.components.base_component import ConfigComponent
from acex.core.models.interfaces import PhysicalInterface, VirtualInterface, SubInterface



class Interface(ConfigComponent): ...


class Physical(Interface):
    type = "ethernetCsmacd"
    model_cls = PhysicalInterface

class SubInterface(ConfigComponent):
    type = "subinterface"
    model_cls = SubInterface


class Loopback(Interface):
    type = "softwareLoopback"
    model_cls = VirtualInterface




