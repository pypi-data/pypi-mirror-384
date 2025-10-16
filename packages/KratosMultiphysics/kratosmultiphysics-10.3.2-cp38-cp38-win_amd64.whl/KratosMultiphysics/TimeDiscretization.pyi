from typing import overload

class BDF:
    def __init__(self, arg0: int) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF, arg0: int) -> None"""
    def ComputeAndSaveBDFCoefficients(self, arg0) -> None:
        """ComputeAndSaveBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: Kratos::ProcessInfo) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: float, arg1: float) -> list[float]

        3. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0: float, arg1: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: float, arg1: float) -> list[float]

        3. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: float, arg1: float) -> list[float]

        3. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF, arg0: Kratos::ProcessInfo) -> list[float]
        """
    def GetTimeOrder(self) -> int:
        """GetTimeOrder(self: Kratos.TimeDiscretization.BDF) -> int"""

class BDF1:
    def __init__(self) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF1) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF1, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF1, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF1, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF1, arg0: Kratos::ProcessInfo) -> list[float]
        """

class BDF2:
    def __init__(self) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF2) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float, arg1: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF2, arg0: float, arg1: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF2, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF2, arg0: float, arg1: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF2, arg0: Kratos::ProcessInfo) -> list[float]
        """

class BDF3:
    def __init__(self) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF3) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF3, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF3, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF3, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF3, arg0: Kratos::ProcessInfo) -> list[float]
        """

class BDF4:
    def __init__(self) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF4) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF4, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF4, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF4, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF4, arg0: Kratos::ProcessInfo) -> list[float]
        """

class BDF5:
    def __init__(self) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF5) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF5, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF5, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF5, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF5, arg0: Kratos::ProcessInfo) -> list[float]
        """

class BDF6:
    def __init__(self) -> None:
        """__init__(self: Kratos.TimeDiscretization.BDF6) -> None"""
    @overload
    def ComputeBDFCoefficients(self, arg0: float) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF6, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF6, arg0: Kratos::ProcessInfo) -> list[float]
        """
    @overload
    def ComputeBDFCoefficients(self, arg0) -> list[float]:
        """ComputeBDFCoefficients(*args, **kwargs)
        Overloaded function.

        1. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF6, arg0: float) -> list[float]

        2. ComputeBDFCoefficients(self: Kratos.TimeDiscretization.BDF6, arg0: Kratos::ProcessInfo) -> list[float]
        """

class Bossak:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.Bossak) -> None

        2. __init__(self: Kratos.TimeDiscretization.Bossak, arg0: float) -> None

        3. __init__(self: Kratos.TimeDiscretization.Bossak, arg0: float, arg1: float, arg2: float) -> None
        """
    @overload
    def __init__(self, arg0: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.Bossak) -> None

        2. __init__(self: Kratos.TimeDiscretization.Bossak, arg0: float) -> None

        3. __init__(self: Kratos.TimeDiscretization.Bossak, arg0: float, arg1: float, arg2: float) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.Bossak) -> None

        2. __init__(self: Kratos.TimeDiscretization.Bossak, arg0: float) -> None

        3. __init__(self: Kratos.TimeDiscretization.Bossak, arg0: float, arg1: float, arg2: float) -> None
        """
    def GetAlphaM(self) -> float:
        """GetAlphaM(self: Kratos.TimeDiscretization.Bossak) -> float"""
    def GetBeta(self) -> float:
        """GetBeta(self: Kratos.TimeDiscretization.Bossak) -> float"""
    def GetGamma(self) -> float:
        """GetGamma(self: Kratos.TimeDiscretization.Bossak) -> float"""

class GeneralizedAlpha:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> None

        2. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha, arg0: float, arg1: float) -> None

        3. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha, arg0: float, arg1: float, arg2: float, arg3: float) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> None

        2. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha, arg0: float, arg1: float) -> None

        3. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha, arg0: float, arg1: float, arg2: float, arg3: float) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> None

        2. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha, arg0: float, arg1: float) -> None

        3. __init__(self: Kratos.TimeDiscretization.GeneralizedAlpha, arg0: float, arg1: float, arg2: float, arg3: float) -> None
        """
    def GetAlphaF(self) -> float:
        """GetAlphaF(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> float"""
    def GetAlphaM(self) -> float:
        """GetAlphaM(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> float"""
    def GetBeta(self) -> float:
        """GetBeta(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> float"""
    def GetGamma(self) -> float:
        """GetGamma(self: Kratos.TimeDiscretization.GeneralizedAlpha) -> float"""

class Newmark:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.Newmark) -> None

        2. __init__(self: Kratos.TimeDiscretization.Newmark, arg0: float, arg1: float) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TimeDiscretization.Newmark) -> None

        2. __init__(self: Kratos.TimeDiscretization.Newmark, arg0: float, arg1: float) -> None
        """
    def GetBeta(self) -> float:
        """GetBeta(self: Kratos.TimeDiscretization.Newmark) -> float"""
    def GetGamma(self) -> float:
        """GetGamma(self: Kratos.TimeDiscretization.Newmark) -> float"""

@overload
def GetMinimumBufferSize(arg0: BDF) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: BDF1) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: BDF2) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: BDF3) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: BDF4) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: BDF5) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: BDF6) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: Newmark) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: Bossak) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
@overload
def GetMinimumBufferSize(arg0: GeneralizedAlpha) -> int:
    """GetMinimumBufferSize(*args, **kwargs)
    Overloaded function.

    1. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF) -> int

    2. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF1) -> int

    3. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF2) -> int

    4. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF3) -> int

    5. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF4) -> int

    6. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF5) -> int

    7. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.BDF6) -> int

    8. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Newmark) -> int

    9. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.Bossak) -> int

    10. GetMinimumBufferSize(arg0: Kratos.TimeDiscretization.GeneralizedAlpha) -> int
    """
