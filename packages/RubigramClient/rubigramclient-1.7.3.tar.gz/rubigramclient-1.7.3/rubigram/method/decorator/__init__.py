from .on_stop import OnStop
from .on_start import OnStart
from .register import Register
from .on_message import OnMessage
from .on_edit_message import OnEditMessage
from .on_delete_message import OnDeleteMessage
from .on_inline_message import OnInlineMessage


class Decorator(
    OnStop,
    OnStart,
    Register,
    OnMessage,
    OnEditMessage,
    OnDeleteMessage,
    OnInlineMessage
):
    pass