# Copyright 2023 Lawrence Livermore National Security, LLC
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from ._file import File
from ._provenance import HardwareProvenance

# pylint: disable=too-many-instance-attributes


@dataclass
class Hardware:
    UUID: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    captureTime: Optional[int] = None
    officialName: Optional[str] = None
    countryOfOrigin: Optional[List[str]] = None
    countryOfOriginSource: Optional[str] = None
    quantity: Optional[int] = None
    description: Optional[str] = None
    vendor: Optional[List[str]] = None
    identifiers: Optional[List[str]] = None
    hardwareType: Optional[List[str]] = None
    comments: Optional[str] = None
    metadata: Optional[List[object]] = None
    supplementaryFiles: Optional[List[File]] = None
    packageType: Optional[str] = None
    boardLocation: Optional[List[str]] = None
    provenance: Optional[List[HardwareProvenance]] = None
    recordedInstitution: Optional[str] = None
