import Kratos
import Kratos.Globals
from typing import Callable, ClassVar, Iterator, overload

__version__: str

class ConnectionStatus:
    __members__: ClassVar[dict] = ...  # read-only
    Connected: ClassVar[ConnectionStatus] = ...
    ConnectionError: ClassVar[ConnectionStatus] = ...
    Disconnected: ClassVar[ConnectionStatus] = ...
    DisconnectionError: ClassVar[ConnectionStatus] = ...
    NotConnected: ClassVar[ConnectionStatus] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: KratosCoSimulationApplication.CoSimIO.ConnectionStatus, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: KratosCoSimulationApplication.CoSimIO.ConnectionStatus) -> int"""
    def __int__(self) -> int:
        """__int__(self: KratosCoSimulationApplication.CoSimIO.ConnectionStatus) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class DoubleVector:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: Buffer) -> None
        """
    @overload
    def __init__(self, arg0: DoubleVector) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: Buffer) -> None
        """
    @overload
    def __init__(self, arg0: list) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: Buffer) -> None
        """
    @overload
    def __init__(self, arg0: Buffer) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: Buffer) -> None
        """
    def append(self, arg0: float) -> None:
        """append(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: float) -> None"""
    def resize(self, arg0: int) -> None:
        """resize(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: int) -> None"""
    def size(self) -> int:
        """size(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> int"""
    def __getitem__(self, arg0: int) -> float:
        """__getitem__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: int) -> float"""
    def __iter__(self) -> Iterator[float]:
        """__iter__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> Iterator[float]"""
    def __len__(self) -> int:
        """__len__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> int"""
    def __setitem__(self, arg0: int, arg1: float) -> None:
        """__setitem__(self: KratosCoSimulationApplication.CoSimIO.DoubleVector, arg0: int, arg1: float) -> None"""

class Info:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.Info) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: KratosCoSimulationApplication.CoSimIO.Info) -> None
        """
    @overload
    def __init__(self, arg0: Info) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.Info) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: KratosCoSimulationApplication.CoSimIO.Info) -> None
        """
    def Clear(self) -> None:
        """Clear(self: KratosCoSimulationApplication.CoSimIO.Info) -> None"""
    def Erase(self, arg0: str) -> None:
        """Erase(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> None"""
    @overload
    def GetBool(self, arg0: str) -> bool:
        """GetBool(*args, **kwargs)
        Overloaded function.

        1. GetBool(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> bool

        2. GetBool(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: bool) -> bool
        """
    @overload
    def GetBool(self, arg0: str, arg1: bool) -> bool:
        """GetBool(*args, **kwargs)
        Overloaded function.

        1. GetBool(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> bool

        2. GetBool(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: bool) -> bool
        """
    @overload
    def GetDouble(self, arg0: str) -> float:
        """GetDouble(*args, **kwargs)
        Overloaded function.

        1. GetDouble(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> float

        2. GetDouble(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: float) -> float
        """
    @overload
    def GetDouble(self, arg0: str, arg1: float) -> float:
        """GetDouble(*args, **kwargs)
        Overloaded function.

        1. GetDouble(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> float

        2. GetDouble(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: float) -> float
        """
    @overload
    def GetInfo(self, arg0: str) -> Info:
        """GetInfo(*args, **kwargs)
        Overloaded function.

        1. GetInfo(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> KratosCoSimulationApplication.CoSimIO.Info

        2. GetInfo(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info
        """
    @overload
    def GetInfo(self, arg0: str, arg1: Info) -> Info:
        """GetInfo(*args, **kwargs)
        Overloaded function.

        1. GetInfo(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> KratosCoSimulationApplication.CoSimIO.Info

        2. GetInfo(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info
        """
    @overload
    def GetInt(self, arg0: str) -> int:
        """GetInt(*args, **kwargs)
        Overloaded function.

        1. GetInt(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> int

        2. GetInt(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: int) -> int
        """
    @overload
    def GetInt(self, arg0: str, arg1: int) -> int:
        """GetInt(*args, **kwargs)
        Overloaded function.

        1. GetInt(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> int

        2. GetInt(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: int) -> int
        """
    @overload
    def GetString(self, arg0: str) -> str:
        """GetString(*args, **kwargs)
        Overloaded function.

        1. GetString(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> str

        2. GetString(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: str) -> str
        """
    @overload
    def GetString(self, arg0: str, arg1: str) -> str:
        """GetString(*args, **kwargs)
        Overloaded function.

        1. GetString(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> str

        2. GetString(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: str) -> str
        """
    def Has(self, arg0: str) -> bool:
        """Has(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str) -> bool"""
    def SetBool(self, arg0: str, arg1: bool) -> None:
        """SetBool(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: bool) -> None"""
    def SetDouble(self, arg0: str, arg1: float) -> None:
        """SetDouble(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: float) -> None"""
    def SetInfo(self, arg0: str, arg1: Info) -> None:
        """SetInfo(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: KratosCoSimulationApplication.CoSimIO.Info) -> None"""
    def SetInt(self, arg0: str, arg1: int) -> None:
        """SetInt(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: int) -> None"""
    def SetString(self, arg0: str, arg1: str) -> None:
        """SetString(self: KratosCoSimulationApplication.CoSimIO.Info, arg0: str, arg1: str) -> None"""
    def Size(self) -> int:
        """Size(self: KratosCoSimulationApplication.CoSimIO.Info) -> int"""
    def __len__(self) -> int:
        """__len__(self: KratosCoSimulationApplication.CoSimIO.Info) -> int"""

class IntVector:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: Buffer) -> None
        """
    @overload
    def __init__(self, arg0: IntVector) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: Buffer) -> None
        """
    @overload
    def __init__(self, arg0: list) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: Buffer) -> None
        """
    @overload
    def __init__(self, arg0: Buffer) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        2. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: KratosCoSimulationApplication.CoSimIO.IntVector) -> None

        3. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: list) -> None

        4. __init__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: Buffer) -> None
        """
    def append(self, arg0: int) -> None:
        """append(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: int) -> None"""
    def resize(self, arg0: int) -> None:
        """resize(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: int) -> None"""
    def size(self) -> int:
        """size(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> int"""
    def __getitem__(self, arg0: int) -> int:
        """__getitem__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: int) -> int"""
    def __iter__(self) -> Iterator[int]:
        """__iter__(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> Iterator[int]"""
    def __len__(self) -> int:
        """__len__(self: KratosCoSimulationApplication.CoSimIO.IntVector) -> int"""
    def __setitem__(self, arg0: int, arg1: int) -> None:
        """__setitem__(self: KratosCoSimulationApplication.CoSimIO.IntVector, arg0: int, arg1: int) -> None"""

def Connect(arg0: Info) -> Info:
    """Connect(arg0: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info"""
def Disconnect(arg0: Info) -> Info:
    """Disconnect(arg0: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info"""
@overload
def ExportData(arg0: Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None:
    """ExportData(*args, **kwargs)
    Overloaded function.

    1. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None

    2. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None

    3. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None
    """
@overload
def ExportData(arg0: Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None:
    """ExportData(*args, **kwargs)
    Overloaded function.

    1. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None

    2. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None

    3. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None
    """
@overload
def ExportData(arg0: Info, arg1: DoubleVector) -> None:
    """ExportData(*args, **kwargs)
    Overloaded function.

    1. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None

    2. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None

    3. ExportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None
    """
def ExportInfo(arg0: Info) -> Info:
    """ExportInfo(arg0: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info"""
def ExportMesh(arg0: Info, arg1: Kratos.ModelPart) -> None:
    """ExportMesh(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart) -> None"""
@overload
def ImportData(arg0: Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None:
    """ImportData(*args, **kwargs)
    Overloaded function.

    1. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None

    2. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None

    3. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None
    """
@overload
def ImportData(arg0: Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None:
    """ImportData(*args, **kwargs)
    Overloaded function.

    1. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None

    2. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None

    3. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None
    """
@overload
def ImportData(arg0: Info, arg1: DoubleVector) -> None:
    """ImportData(*args, **kwargs)
    Overloaded function.

    1. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.Globals.DataLocation) -> None

    2. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Globals.DataLocation) -> None

    3. ImportData(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: KratosCoSimulationApplication.CoSimIO.DoubleVector) -> None
    """
def ImportInfo(arg0: Info) -> Info:
    """ImportInfo(arg0: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info"""
def ImportMesh(arg0: Info, arg1: Kratos.ModelPart, arg2: Kratos.DataCommunicator) -> None:
    """ImportMesh(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Kratos.ModelPart, arg2: Kratos.DataCommunicator) -> None"""
def InfoFromParameters(arg0: Kratos.Parameters) -> Info:
    """InfoFromParameters(arg0: Kratos.Parameters) -> KratosCoSimulationApplication.CoSimIO.Info"""
def Register(arg0: Info, arg1: Callable[[Info], Info]) -> Info:
    """Register(arg0: KratosCoSimulationApplication.CoSimIO.Info, arg1: Callable[[KratosCoSimulationApplication.CoSimIO.Info], KratosCoSimulationApplication.CoSimIO.Info]) -> KratosCoSimulationApplication.CoSimIO.Info"""
def Run(arg0: Info) -> Info:
    """Run(arg0: KratosCoSimulationApplication.CoSimIO.Info) -> KratosCoSimulationApplication.CoSimIO.Info"""
