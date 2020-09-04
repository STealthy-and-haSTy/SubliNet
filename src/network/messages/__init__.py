from ....sublinet import reload

reload('src.network.messages', ["base", "introduction", "acknowledge",
                                "message", "error", "clipboard", "filecontent"])

from .base import ProtocolMessage
from .introduction import IntroductionMessage
from .acknowledge import AcknowledgeMessage
from .message import MessageMessage
from .error import ErrorMessage
from .clipboard import ClipboardMessage
from .filecontent import FileContentMessage


ProtocolMessage.register(IntroductionMessage)
ProtocolMessage.register(AcknowledgeMessage)
ProtocolMessage.register(MessageMessage)
ProtocolMessage.register(ErrorMessage)
ProtocolMessage.register(ClipboardMessage)
ProtocolMessage.register(FileContentMessage)


__all__ = [
    "ProtocolMessage",

    "IntroductionMessage",
    "AcknowledgeMessage",

    "MessageMessage",
    "ErrorMessage",

    "ClipboardMessage",
    "FileContentMessage"
]
