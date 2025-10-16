import Kratos
from . import CoSimIO as CoSimIO, EMPIRE_API as EMPIRE_API
from typing import ClassVar, overload

class ConversionUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @overload
    @staticmethod
    def ConvertElementalDataToNodalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None:
        """ConvertElementalDataToNodalDataDirect(*args, **kwargs)
        Overloaded function.

        1. ConvertElementalDataToNodalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertElementalDataToNodalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertElementalDataToNodalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
        """ConvertElementalDataToNodalDataDirect(*args, **kwargs)
        Overloaded function.

        1. ConvertElementalDataToNodalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertElementalDataToNodalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertElementalDataToNodalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None:
        """ConvertElementalDataToNodalDataTranspose(*args, **kwargs)
        Overloaded function.

        1. ConvertElementalDataToNodalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertElementalDataToNodalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertElementalDataToNodalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
        """ConvertElementalDataToNodalDataTranspose(*args, **kwargs)
        Overloaded function.

        1. ConvertElementalDataToNodalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertElementalDataToNodalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertNodalDataToElementalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None:
        """ConvertNodalDataToElementalDataDirect(*args, **kwargs)
        Overloaded function.

        1. ConvertNodalDataToElementalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertNodalDataToElementalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertNodalDataToElementalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
        """ConvertNodalDataToElementalDataDirect(*args, **kwargs)
        Overloaded function.

        1. ConvertNodalDataToElementalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertNodalDataToElementalDataDirect(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertNodalDataToElementalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None:
        """ConvertNodalDataToElementalDataTranspose(*args, **kwargs)
        Overloaded function.

        1. ConvertNodalDataToElementalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertNodalDataToElementalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def ConvertNodalDataToElementalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
        """ConvertNodalDataToElementalDataTranspose(*args, **kwargs)
        Overloaded function.

        1. ConvertNodalDataToElementalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable) -> None

        2. ConvertNodalDataToElementalDataTranspose(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None
        """

class DataTransfer3D1DProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.DataTransfer3D1DProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosCoSimulationApplication.DataTransfer3D1DProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCoSimulationApplication.DataTransfer3D1DProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosCoSimulationApplication.DataTransfer3D1DProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """

class FetiDynamicCouplingUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def EquilibrateDomains(self) -> None:
        """EquilibrateDomains(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities) -> None"""
    def SetEffectiveStiffnessMatrixExplicit(self, *args, **kwargs):
        """SetEffectiveStiffnessMatrixExplicit(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities, arg0: Kratos::FetiDynamicCouplingUtilities<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > >::SolverIndex) -> None"""
    def SetEffectiveStiffnessMatrixImplicit(self, *args, **kwargs):
        """SetEffectiveStiffnessMatrixImplicit(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities, arg0: Kratos.CompressedMatrix, arg1: Kratos::FetiDynamicCouplingUtilities<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > >::SolverIndex) -> None"""
    def SetLinearSolver(self, arg0: Kratos.LinearSolver) -> None:
        """SetLinearSolver(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities, arg0: Kratos.LinearSolver) -> None"""
    def SetMappingMatrix(self, arg0: Kratos.CompressedMatrix) -> None:
        """SetMappingMatrix(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities, arg0: Kratos.CompressedMatrix) -> None"""
    def SetOriginAndDestinationDomainsWithInterfaceModelParts(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """SetOriginAndDestinationDomainsWithInterfaceModelParts(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def SetOriginInitialKinematics(self) -> None:
        """SetOriginInitialKinematics(self: KratosCoSimulationApplication.FetiDynamicCouplingUtilities) -> None"""

class FetiSolverIndexType:
    """Members:

      Origin

      Destination"""
    __members__: ClassVar[dict] = ...  # read-only
    Destination: ClassVar[FetiSolverIndexType] = ...
    Origin: ClassVar[FetiSolverIndexType] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: KratosCoSimulationApplication.FetiSolverIndexType, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: KratosCoSimulationApplication.FetiSolverIndexType) -> int"""
    def __int__(self) -> int:
        """__int__(self: KratosCoSimulationApplication.FetiSolverIndexType) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: object) -> str

        name(self: object) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: KratosCoSimulationApplication.FetiSolverIndexType) -> int"""

class KratosCoSimulationApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosCoSimulationApplication.KratosCoSimulationApplication) -> None"""
