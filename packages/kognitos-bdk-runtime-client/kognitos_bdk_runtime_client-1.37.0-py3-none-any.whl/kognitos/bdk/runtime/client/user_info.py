from dataclasses import dataclass
from typing import Dict, Optional

from kognitos.bdk.runtime.client.base import BdkDescriptorBase


@dataclass
class UserInfo(BdkDescriptorBase):
    email: Optional[str]
    username: Optional[str]
    other_attributes: Dict[str, str]
