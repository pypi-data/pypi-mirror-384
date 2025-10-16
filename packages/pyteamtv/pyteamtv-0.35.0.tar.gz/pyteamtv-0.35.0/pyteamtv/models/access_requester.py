from dataclasses import dataclass
from typing import List


@dataclass
class AccessRequester:
    user_id: str
    tenant_id: str
    resource_group_id: str
    role_names: List[str]
