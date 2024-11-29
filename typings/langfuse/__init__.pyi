"""Type stubs for langfuse"""

from typing import Any, Optional

class Langfuse:
    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: Optional[str] = None,
        debug: bool = False,
    ) -> None: ...
    def trace(self, name: str, **kwargs: Any) -> Any: ...
