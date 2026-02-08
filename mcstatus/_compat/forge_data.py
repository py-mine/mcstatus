from mcstatus._utils import deprecation_warn
from mcstatus.responses.forge import ForgeData, ForgeDataChannel, ForgeDataMod

__all__ = [
    "ForgeData",
    "ForgeDataChannel",
    "ForgeDataMod",
]

deprecation_warn(
    obj_name="mcstatus.forge_data",
    removal_version="14.0.0",
    replacement="mcstatus.responses.forge",
)
