from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from midpoint_cli.client import MidpointClient


class PromptBase:
    def __init__(self):
        # Note: self.client gets set immediately in MidpointClientPrompt.__init__()
        # This is just a type declaration - the actual assignment happens in the subclass
        self.client: MidpointClient
        self.error_code: Optional[int] = None
        self.error_message: Optional[str] = None
