import Kratos
from typing import overload

def EMPIRE_API_Connect(arg0: str) -> None:
    """EMPIRE_API_Connect(arg0: str) -> None"""
def EMPIRE_API_Disconnect() -> None:
    """EMPIRE_API_Disconnect() -> None"""
def EMPIRE_API_PrintTiming(arg0: bool) -> None:
    """EMPIRE_API_PrintTiming(arg0: bool) -> None"""
def EMPIRE_API_SetEchoLevel(arg0: int) -> None:
    """EMPIRE_API_SetEchoLevel(arg0: int) -> None"""
def EMPIRE_API_getUserDefinedText(arg0: str) -> str:
    """EMPIRE_API_getUserDefinedText(arg0: str) -> str"""
def EMPIRE_API_recvConvergenceSignal(file_name_extension: str = ...) -> int:
    """EMPIRE_API_recvConvergenceSignal(file_name_extension: str = 'default') -> int"""
@overload
def EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_recvDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvDataField(arg0: str, arg1: int, arg2: list) -> None

    2. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_recvDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_recvMesh(model_part: Kratos.ModelPart, name: str, use_conditions: bool = ..., use_raw_pointers: bool = ...) -> None:
    """EMPIRE_API_recvMesh(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvMesh(model_part: Kratos.ModelPart, name: str, use_conditions: bool = False, use_raw_pointers: bool = False) -> None

    2. EMPIRE_API_recvMesh(model_part: Kratos.ModelPart, use_conditions: bool = False, use_raw_pointers: bool = False) -> None
    """
@overload
def EMPIRE_API_recvMesh(model_part: Kratos.ModelPart, use_conditions: bool = ..., use_raw_pointers: bool = ...) -> None:
    """EMPIRE_API_recvMesh(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_recvMesh(model_part: Kratos.ModelPart, name: str, use_conditions: bool = False, use_raw_pointers: bool = False) -> None

    2. EMPIRE_API_recvMesh(model_part: Kratos.ModelPart, use_conditions: bool = False, use_raw_pointers: bool = False) -> None
    """
def EMPIRE_API_recvSignal_double(arg0: str, arg1: int, arg2: list) -> None:
    """EMPIRE_API_recvSignal_double(arg0: str, arg1: int, arg2: list) -> None"""
def EMPIRE_API_sendConvergenceSignal(signal: int, file_name_extension: str = ...) -> None:
    """EMPIRE_API_sendConvergenceSignal(signal: int, file_name_extension: str = 'default') -> None"""
@overload
def EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
    """EMPIRE_API_sendDataField(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendDataField(arg0: str, arg1: int, arg2: list[float]) -> None

    2. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable) -> None

    3. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

    4. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3) -> None

    5. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

    6. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None

    7. EMPIRE_API_sendDataField(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
    """
@overload
def EMPIRE_API_sendMesh(model_part: Kratos.ModelPart, name: str, use_conditions: bool = ...) -> None:
    """EMPIRE_API_sendMesh(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendMesh(model_part: Kratos.ModelPart, name: str, use_conditions: bool = False) -> None

    2. EMPIRE_API_sendMesh(model_part: Kratos.ModelPart, use_conditions: bool = False) -> None
    """
@overload
def EMPIRE_API_sendMesh(model_part: Kratos.ModelPart, use_conditions: bool = ...) -> None:
    """EMPIRE_API_sendMesh(*args, **kwargs)
    Overloaded function.

    1. EMPIRE_API_sendMesh(model_part: Kratos.ModelPart, name: str, use_conditions: bool = False) -> None

    2. EMPIRE_API_sendMesh(model_part: Kratos.ModelPart, use_conditions: bool = False) -> None
    """
def EMPIRE_API_sendSignal_double(arg0: str, arg1: int, arg2: list[float]) -> None:
    """EMPIRE_API_sendSignal_double(arg0: str, arg1: int, arg2: list[float]) -> None"""
