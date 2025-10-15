import Kratos
from typing import overload

@overload
def GetRegisteredName(arg0: Kratos.Element) -> str:
    """GetRegisteredName(*args, **kwargs)
    Overloaded function.

    1. GetRegisteredName(arg0: Kratos.Element) -> str

    2. GetRegisteredName(arg0: Kratos.Condition) -> str
    """
@overload
def GetRegisteredName(arg0: Kratos.Condition) -> str:
    """GetRegisteredName(*args, **kwargs)
    Overloaded function.

    1. GetRegisteredName(arg0: Kratos.Element) -> str

    2. GetRegisteredName(arg0: Kratos.Condition) -> str
    """
