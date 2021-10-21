# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import asyncio
from enum import Enum

import psutil
from pydantic import BaseModel, Field

# Minimum requirements for individual host validation:
# NOTE(jhesketh): These are obviously hardcoded for the moment, but may be
#                 better moved into some kind of support matrix (eg feature
#                 vs hardware etc).
#                 These are also currently somewhat arbitrary and will need
#                 tuning.
AQUARIUM_MIN_CPU_THREADS = 2
AQUARIUM_MIN_MEMORY = 2 * 1024 * 1024 * 1024  # 2 * KB * MB * GB
AQUARIUM_MIN_ROOT_DISK = 10 * 1024 * 1024 * 1024  # 2 * KB * MB * GB


class CPUQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_CORES = 1


class CPUQualifiedModel(BaseModel):
    qualified: bool = Field("The CPU is sufficient")
    min_threads: int = Field("Minimum number of CPU threads")
    actual_threads: int = Field("Actual number of CPU threads")
    error: str = Field("CPU didn't meet requirements")
    status: CPUQualifiedEnum = Field(CPUQualifiedEnum.QUALIFIED)


class MemoryQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_MEMORY = 1


class MemoryQualifiedModel(BaseModel):
    qualified: bool = Field("The memory is sufficient")
    min_mem: int = Field("Minimum amount of memory (bytes)")
    actual_mem: int = Field("Actual amount of memory (bytes)")
    error: str = Field("Memory didn't meet requirements")
    status: MemoryQualifiedEnum = Field(MemoryQualifiedEnum.QUALIFIED)


class RootDiskQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_SPACE = 1


class RootDiskQualifiedModel(BaseModel):
    qualified: bool = Field("The root disk size is sufficient")
    min_disk: int = Field("Minimum size of root disk (bytes)")
    actual_disk: int = Field("Actual size of root disk (bytes)")
    error: str = Field("Root disk didn't meet requirements")
    status: RootDiskQualifiedEnum = Field(RootDiskQualifiedEnum.QUALIFIED)


class LocalhostQualifiedModel(BaseModel):
    all_qualified: bool = Field("The localhost passes validation")
    cpu_qualified: CPUQualifiedModel = Field("CPU qualification details")
    mem_qualified: MemoryQualifiedModel = Field("Memory qualification details")
    root_disk_qualified: RootDiskQualifiedModel = Field(
        "Root disk qualification details"
    )


async def validate_cpu() -> CPUQualifiedModel:
    """
    Validates the localhost meets the minium CPU requirements.
    """
    qualified: bool = True
    min_threads: int = AQUARIUM_MIN_CPU_THREADS
    actual_threads: int = psutil.cpu_count()
    error: str = ""
    status: CPUQualifiedEnum = CPUQualifiedEnum.QUALIFIED

    if actual_threads < min_threads:
        qualified = False
        error = (
            "The node does not have a sufficient number of CPU cores. "
            "Required: %d, Actual: %d." % (min_threads, actual_threads)
        )
        status = CPUQualifiedEnum.INSUFFICIENT_CORES

    return CPUQualifiedModel(
        qualified=qualified,
        min_threads=min_threads,
        actual_threads=actual_threads,
        error=error,
        status=status,
    )


async def validate_memory() -> MemoryQualifiedModel:
    """
    Validates the localhost meets the minium memory requirements.
    """
    qualified: bool = True
    min_mem: int = AQUARIUM_MIN_MEMORY
    actual_mem: int = psutil.virtual_memory().total
    error: str = ""
    status: MemoryQualifiedEnum = MemoryQualifiedEnum.QUALIFIED

    if actual_mem < min_mem:
        qualified = False
        # 1024 kb / 1024 mb / 1024 gb
        # NOTE(jhesketh): We round down to the nearest GB
        min_mem_gb: int = int(min_mem / 1024 / 1024 / 1024)
        actual_mem_gb: int = int(actual_mem / 1024 / 1024 / 1024)
        error = (
            "The node does not have a sufficient memory. "
            "Required: %dGB, Actual: %dGB." % (min_mem_gb, actual_mem_gb)
        )
        status = MemoryQualifiedEnum.INSUFFICIENT_MEMORY
    return MemoryQualifiedModel(
        qualified=qualified,
        min_mem=min_mem,
        actual_mem=actual_mem,
        error=error,
        status=status,
    )


async def validate_root_disk() -> RootDiskQualifiedModel:
    """
    Validates the localhost meets the minium disk requirements.

    NOTE: This only verifies the total size of the root partition. It does
          not validate the amount of free space etc.
    """
    qualified: bool = True
    min_disk: int = AQUARIUM_MIN_ROOT_DISK
    actual_disk: int = psutil.disk_usage("/").total
    error: str = ""
    status: RootDiskQualifiedEnum = RootDiskQualifiedEnum.QUALIFIED

    if actual_disk < min_disk:
        qualified = False
        # 1024 kb / 1024 mb / 1024 gb
        # NOTE(jhesketh): We round down to the nearest GB
        min_disk_gb: int = int(min_disk / 1024 / 1024 / 1024)
        actual_disk_gb: int = int(actual_disk / 1024 / 1024 / 1024)
        error = (
            "The node does not have sufficient space on the root disk. "
            "Required: %dGB, Actual: %dGB." % (min_disk_gb, actual_disk_gb)
        )
        status = RootDiskQualifiedEnum.INSUFFICIENT_SPACE
    return RootDiskQualifiedModel(
        qualified=qualified,
        min_disk=min_disk,
        actual_disk=actual_disk,
        error=error,
        status=status,
    )


async def localhost_qualified() -> LocalhostQualifiedModel:
    """
    Validates whether the localhost is fully qualified (ie, meets all minium
    requirements).
    """
    all_qualified: bool = True

    cpu_qualified: CPUQualifiedModel
    mem_qualified: MemoryQualifiedModel
    root_disk_qualified: RootDiskQualifiedModel
    cpu_qualified, mem_qualified, root_disk_qualified = await asyncio.gather(
        validate_cpu(), validate_memory(), validate_root_disk()
    )

    if not (
        cpu_qualified.qualified
        and mem_qualified.qualified
        and root_disk_qualified.qualified
    ):
        all_qualified = False

    result = LocalhostQualifiedModel(
        all_qualified=all_qualified,
        cpu_qualified=cpu_qualified,
        mem_qualified=mem_qualified,
        root_disk_qualified=root_disk_qualified,
    )
    return result