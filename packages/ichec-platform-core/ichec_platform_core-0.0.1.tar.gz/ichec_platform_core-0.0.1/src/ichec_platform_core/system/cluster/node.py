from pydantic import BaseModel

from ichec_platform_core.system.cpu import PhysicalProcessor
from ichec_platform_core.system.gpu import GpuProcessor


class ComputeNode(BaseModel, frozen=True):

    address: str
    cpus: list[PhysicalProcessor] = []
    gpus: list[GpuProcessor] = []
