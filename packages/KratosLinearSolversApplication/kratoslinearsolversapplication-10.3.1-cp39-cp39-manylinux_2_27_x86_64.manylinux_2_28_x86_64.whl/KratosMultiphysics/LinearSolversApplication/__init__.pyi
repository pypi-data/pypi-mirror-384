import Kratos
from typing import overload

class ComplexDenseColPivHouseholderQRSolver(ComplexDirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDenseColPivHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDenseColPivHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDenseColPivHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDenseColPivHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """

class ComplexDenseHouseholderQRSolver(ComplexDirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDenseHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDenseHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDenseHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDenseHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """

class ComplexDenseLinearSolver:
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.ComplexDenseLinearSolver) -> None"""
    def Clear(self) -> None:
        """Clear(self: KratosLinearSolversApplication.ComplexDenseLinearSolver) -> None"""
    def Initialize(self, arg0: Kratos.ComplexMatrix, arg1: Kratos.ComplexVector, arg2: Kratos.ComplexVector) -> None:
        """Initialize(self: KratosLinearSolversApplication.ComplexDenseLinearSolver, arg0: Kratos.ComplexMatrix, arg1: Kratos.ComplexVector, arg2: Kratos.ComplexVector) -> None"""
    def Solve(self, arg0: Kratos.ComplexMatrix, arg1: Kratos.ComplexVector, arg2: Kratos.ComplexVector) -> bool:
        """Solve(self: KratosLinearSolversApplication.ComplexDenseLinearSolver, arg0: Kratos.ComplexMatrix, arg1: Kratos.ComplexVector, arg2: Kratos.ComplexVector) -> bool"""

class ComplexDenseLinearSolverFactory:
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.ComplexDenseLinearSolverFactory) -> None"""
    def Create(self, arg0: Kratos.Parameters) -> ComplexDenseLinearSolver:
        """Create(self: KratosLinearSolversApplication.ComplexDenseLinearSolverFactory, arg0: Kratos.Parameters) -> KratosLinearSolversApplication.ComplexDenseLinearSolver"""
    def Has(self, arg0: str) -> bool:
        """Has(self: KratosLinearSolversApplication.ComplexDenseLinearSolverFactory, arg0: str) -> bool"""

class ComplexDensePartialPivLUSolver(ComplexDirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDensePartialPivLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDensePartialPivLUSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDensePartialPivLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDensePartialPivLUSolver, arg0: Kratos.Parameters) -> None
        """

class ComplexDirectSolver(ComplexDenseLinearSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDirectSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDirectSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexDirectSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexDirectSolver, arg0: Kratos.Parameters) -> None
        """

class ComplexSparseLUSolver(Kratos.ComplexDirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexSparseLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexSparseLUSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.ComplexSparseLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.ComplexSparseLUSolver, arg0: Kratos.Parameters) -> None
        """

class DenseColPivHouseholderQRSolver(DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DenseColPivHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DenseColPivHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DenseColPivHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DenseColPivHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """

class DenseEigenvalueSolver(DenseLinearSolver):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosLinearSolversApplication.DenseEigenvalueSolver, arg0: Kratos.Parameters) -> None"""
    def Solve(self, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Vector, arg3: Kratos.Matrix) -> None:
        """Solve(self: KratosLinearSolversApplication.DenseEigenvalueSolver, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Vector, arg3: Kratos.Matrix) -> None"""

class DenseHouseholderQRSolver(DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DenseHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DenseHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DenseHouseholderQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DenseHouseholderQRSolver, arg0: Kratos.Parameters) -> None
        """

class DenseLLTSolver(DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DenseLLTSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DenseLLTSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DenseLLTSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DenseLLTSolver, arg0: Kratos.Parameters) -> None
        """

class DenseLinearSolver:
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.DenseLinearSolver) -> None"""
    def Clear(self) -> None:
        """Clear(self: KratosLinearSolversApplication.DenseLinearSolver) -> None"""
    def Initialize(self, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Vector) -> None:
        """Initialize(self: KratosLinearSolversApplication.DenseLinearSolver, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Vector) -> None"""
    @overload
    def Solve(self, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Vector) -> bool:
        """Solve(*args, **kwargs)
        Overloaded function.

        1. Solve(self: KratosLinearSolversApplication.DenseLinearSolver, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Vector) -> bool

        2. Solve(self: KratosLinearSolversApplication.DenseLinearSolver, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Matrix) -> bool
        """
    @overload
    def Solve(self, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Matrix) -> bool:
        """Solve(*args, **kwargs)
        Overloaded function.

        1. Solve(self: KratosLinearSolversApplication.DenseLinearSolver, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Vector) -> bool

        2. Solve(self: KratosLinearSolversApplication.DenseLinearSolver, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Matrix) -> bool
        """

class DenseLinearSolverFactory:
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.DenseLinearSolverFactory) -> None"""
    def Create(self, arg0: Kratos.Parameters) -> DenseLinearSolver:
        """Create(self: KratosLinearSolversApplication.DenseLinearSolverFactory, arg0: Kratos.Parameters) -> KratosLinearSolversApplication.DenseLinearSolver"""
    def Has(self, arg0: str) -> bool:
        """Has(self: KratosLinearSolversApplication.DenseLinearSolverFactory, arg0: str) -> bool"""

class DensePartialPivLUSolver(DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DensePartialPivLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DensePartialPivLUSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DensePartialPivLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DensePartialPivLUSolver, arg0: Kratos.Parameters) -> None
        """

class DirectSolver(DenseLinearSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DirectSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DirectSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.DirectSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.DirectSolver, arg0: Kratos.Parameters) -> None
        """

class EigenDenseBDCSVD(Kratos.DenseSingularValueDecomposition):
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.EigenDenseBDCSVD) -> None"""
    @overload
    def Compute(self, arg0: Kratos.Matrix, arg1: Kratos.Parameters) -> None:
        """Compute(*args, **kwargs)
        Overloaded function.

        1. Compute(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Matrix, arg1: Kratos.Parameters) -> None

        2. Compute(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Parameters) -> None
        """
    @overload
    def Compute(self, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Parameters) -> None:
        """Compute(*args, **kwargs)
        Overloaded function.

        1. Compute(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Matrix, arg1: Kratos.Parameters) -> None

        2. Compute(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Parameters) -> None
        """
    def MatrixU(self, arg0: Kratos.Matrix) -> None:
        """MatrixU(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Matrix) -> None"""
    def MatrixV(self, arg0: Kratos.Matrix) -> None:
        """MatrixV(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Matrix) -> None"""
    def NonZeroSingularValues(self) -> int:
        """NonZeroSingularValues(self: KratosLinearSolversApplication.EigenDenseBDCSVD) -> int"""
    def Rank(self) -> int:
        """Rank(self: KratosLinearSolversApplication.EigenDenseBDCSVD) -> int"""
    def SetThreshold(self, arg0: float) -> None:
        """SetThreshold(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: float) -> None"""
    def SingularValues(self, arg0: Kratos.Vector) -> None:
        """SingularValues(self: KratosLinearSolversApplication.EigenDenseBDCSVD, arg0: Kratos.Vector) -> None"""

class EigenDenseColumnPivotingHouseholderQRDecomposition(Kratos.DenseQRDecompositionType):
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition) -> None"""
    @overload
    def Compute(self, arg0: Kratos.Matrix) -> None:
        """Compute(*args, **kwargs)
        Overloaded function.

        1. Compute(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None

        2. Compute(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Matrix) -> None
        """
    @overload
    def Compute(self, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Matrix) -> None:
        """Compute(*args, **kwargs)
        Overloaded function.

        1. Compute(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None

        2. Compute(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix, arg1: Kratos.Matrix, arg2: Kratos.Matrix) -> None
        """
    def MatrixP(self, arg0: Kratos.Matrix) -> None:
        """MatrixP(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None"""
    def MatrixQ(self, arg0: Kratos.Matrix) -> None:
        """MatrixQ(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None"""
    def MatrixR(self, arg0: Kratos.Matrix) -> None:
        """MatrixR(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None"""
    def Rank(self) -> int:
        """Rank(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition) -> int"""
    @overload
    def Solve(self, arg0: Kratos.Matrix, arg1: Kratos.Matrix) -> None:
        """Solve(*args, **kwargs)
        Overloaded function.

        1. Solve(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix, arg1: Kratos.Matrix) -> None

        2. Solve(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Vector, arg1: Kratos.Vector) -> None
        """
    @overload
    def Solve(self, arg0: Kratos.Vector, arg1: Kratos.Vector) -> None:
        """Solve(*args, **kwargs)
        Overloaded function.

        1. Solve(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Matrix, arg1: Kratos.Matrix) -> None

        2. Solve(self: KratosLinearSolversApplication.EigenDenseColumnPivotingHouseholderQRDecomposition, arg0: Kratos.Vector, arg1: Kratos.Vector) -> None
        """

class EigenDenseHouseholderQRDecomposition(Kratos.DenseQRDecompositionType):
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition) -> None"""
    def Compute(self, arg0: Kratos.Matrix) -> None:
        """Compute(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None"""
    def MatrixQ(self, arg0: Kratos.Matrix) -> None:
        """MatrixQ(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None"""
    def MatrixR(self, arg0: Kratos.Matrix) -> None:
        """MatrixR(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Matrix) -> None"""
    @overload
    def Solve(self, arg0: Kratos.Matrix, arg1: Kratos.Matrix) -> None:
        """Solve(*args, **kwargs)
        Overloaded function.

        1. Solve(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Matrix, arg1: Kratos.Matrix) -> None

        2. Solve(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Vector, arg1: Kratos.Vector) -> None
        """
    @overload
    def Solve(self, arg0: Kratos.Vector, arg1: Kratos.Vector) -> None:
        """Solve(*args, **kwargs)
        Overloaded function.

        1. Solve(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Matrix, arg1: Kratos.Matrix) -> None

        2. Solve(self: KratosLinearSolversApplication.EigenDenseHouseholderQRDecomposition, arg0: Kratos.Vector, arg1: Kratos.Vector) -> None
        """

class EigenDenseJacobiSVD(Kratos.DenseSingularValueDecomposition):
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.EigenDenseJacobiSVD) -> None"""
    @overload
    def Compute(self, arg0: Kratos.Matrix, arg1: Kratos.Parameters) -> None:
        """Compute(*args, **kwargs)
        Overloaded function.

        1. Compute(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Matrix, arg1: Kratos.Parameters) -> None

        2. Compute(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Parameters) -> None
        """
    @overload
    def Compute(self, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Parameters) -> None:
        """Compute(*args, **kwargs)
        Overloaded function.

        1. Compute(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Matrix, arg1: Kratos.Parameters) -> None

        2. Compute(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Matrix, arg1: Kratos.Vector, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Parameters) -> None
        """
    def MatrixU(self, arg0: Kratos.Matrix) -> None:
        """MatrixU(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Matrix) -> None"""
    def MatrixV(self, arg0: Kratos.Matrix) -> None:
        """MatrixV(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Matrix) -> None"""
    def NonZeroSingularValues(self) -> int:
        """NonZeroSingularValues(self: KratosLinearSolversApplication.EigenDenseJacobiSVD) -> int"""
    def Rank(self) -> int:
        """Rank(self: KratosLinearSolversApplication.EigenDenseJacobiSVD) -> int"""
    def SetThreshold(self, arg0: float) -> None:
        """SetThreshold(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: float) -> None"""
    def SingularValues(self, arg0: Kratos.Vector) -> None:
        """SingularValues(self: KratosLinearSolversApplication.EigenDenseJacobiSVD, arg0: Kratos.Vector) -> None"""

class EigensystemSolver(Kratos.LinearSolver):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosLinearSolversApplication.EigensystemSolver, arg0: Kratos.Parameters) -> None"""

class FEASTConditionNumberUtility:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def GetConditionNumber(self) -> float:
        """GetConditionNumber(self: Kratos.CompressedMatrix) -> float"""

class KratosLinearSolversApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosLinearSolversApplication.KratosLinearSolversApplication) -> None"""

class SparseCGSolver(Kratos.DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.SparseCGSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.SparseCGSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.SparseCGSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.SparseCGSolver, arg0: Kratos.Parameters) -> None
        """

class SparseLUSolver(Kratos.DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.SparseLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.SparseLUSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.SparseLUSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.SparseLUSolver, arg0: Kratos.Parameters) -> None
        """

class SparseQRSolver(Kratos.DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.SparseQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.SparseQRSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosLinearSolversApplication.SparseQRSolver) -> None

        2. __init__(self: KratosLinearSolversApplication.SparseQRSolver, arg0: Kratos.Parameters) -> None
        """

class SpectraSymGEigsShiftSolver(Kratos.LinearSolver):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosLinearSolversApplication.SpectraSymGEigsShiftSolver, arg0: Kratos.Parameters) -> None"""

def HasFEAST() -> bool:
    """HasFEAST() -> bool"""
def HasMKL() -> bool:
    """HasMKL() -> bool"""
