import Kratos
import Kratos.TimeDiscretization
from typing import overload

class AffineTransform:
    @overload
    def __init__(self, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None

        3. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Array3, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None

        3. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Quaternion, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None

        3. __init__(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None
        """
    def Apply(self, arg0: Kratos.Array3) -> Kratos.Array3:
        """Apply(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3) -> Kratos.Array3"""
    @overload
    def SetRotation(self, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None:
        """SetRotation(*args, **kwargs)
        Overloaded function.

        1. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        2. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        3. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3) -> None

        4. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3) -> None
        """
    @overload
    def SetRotation(self, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None:
        """SetRotation(*args, **kwargs)
        Overloaded function.

        1. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        2. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        3. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3) -> None

        4. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3) -> None
        """
    @overload
    def SetRotation(self, arg0: Kratos.Array3, arg1: Kratos.Array3) -> None:
        """SetRotation(*args, **kwargs)
        Overloaded function.

        1. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        2. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        3. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3) -> None

        4. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3) -> None
        """
    @overload
    def SetRotation(self, arg0: Kratos.Quaternion, arg1: Kratos.Array3) -> None:
        """SetRotation(*args, **kwargs)
        Overloaded function.

        1. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        2. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: float, arg2: Kratos.Array3) -> None

        3. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3, arg1: Kratos.Array3) -> None

        4. SetRotation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Quaternion, arg1: Kratos.Array3) -> None
        """
    def SetTranslation(self, arg0: Kratos.Array3) -> None:
        """SetTranslation(self: KratosMeshMovingApplication.AffineTransform, arg0: Kratos.Array3) -> None"""

class FixedMeshALEUtilities:
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosMeshMovingApplication.FixedMeshALEUtilities, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""
    def ComputeMeshMovement(self, arg0: float) -> None:
        """ComputeMeshMovement(self: KratosMeshMovingApplication.FixedMeshALEUtilities, arg0: float) -> None"""
    def Initialize(self, arg0: Kratos.ModelPart) -> None:
        """Initialize(self: KratosMeshMovingApplication.FixedMeshALEUtilities, arg0: Kratos.ModelPart) -> None"""
    def ProjectVirtualValues2D(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """ProjectVirtualValues2D(self: KratosMeshMovingApplication.FixedMeshALEUtilities, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def ProjectVirtualValues3D(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """ProjectVirtualValues3D(self: KratosMeshMovingApplication.FixedMeshALEUtilities, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def SetVirtualMeshValuesFromOriginMesh(self) -> None:
        """SetVirtualMeshValuesFromOriginMesh(self: KratosMeshMovingApplication.FixedMeshALEUtilities) -> None"""
    def UndoMeshMovement(self) -> None:
        """UndoMeshMovement(self: KratosMeshMovingApplication.FixedMeshALEUtilities) -> None"""

class KratosMeshMovingApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosMeshMovingApplication.KratosMeshMovingApplication) -> None"""

class LaplacianMeshMovingStrategy(Kratos.ImplicitSolvingStrategy):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.LaplacianMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int) -> None

        2. __init__(self: KratosMeshMovingApplication.LaplacianMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.LaplacianMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int) -> None

        2. __init__(self: KratosMeshMovingApplication.LaplacianMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: bool) -> None
        """

class ParametricAffineTransform:
    @overload
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.ParametricAffineTransform, arg0: Kratos.Parameters, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshMovingApplication.ParametricAffineTransform, arg0: Kratos.Parameters, arg1: Kratos.Parameters, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.Parameters, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.ParametricAffineTransform, arg0: Kratos.Parameters, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshMovingApplication.ParametricAffineTransform, arg0: Kratos.Parameters, arg1: Kratos.Parameters, arg2: Kratos.Parameters) -> None
        """
    def Apply(self, arg0: Kratos.Array3, arg1: float, arg2: float, arg3: float, arg4: float) -> Kratos.Array3:
        """Apply(self: KratosMeshMovingApplication.ParametricAffineTransform, arg0: Kratos.Array3, arg1: float, arg2: float, arg3: float, arg4: float) -> Kratos.Array3"""

class StructuralMeshMovingStrategy(Kratos.ImplicitSolvingStrategy):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.StructuralMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: float) -> None

        2. __init__(self: KratosMeshMovingApplication.StructuralMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: float, arg8: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: float, arg8: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshMovingApplication.StructuralMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: float) -> None

        2. __init__(self: KratosMeshMovingApplication.StructuralMeshMovingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: int, arg7: float, arg8: bool) -> None
        """

@overload
def CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF1) -> None:
    """CalculateMeshVelocities(*args, **kwargs)
    Overloaded function.

    1. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF1) -> None

    2. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF2) -> None

    3. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Newmark) -> None

    4. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Bossak) -> None

    5. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.GeneralizedAlpha) -> None
    """
@overload
def CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF2) -> None:
    """CalculateMeshVelocities(*args, **kwargs)
    Overloaded function.

    1. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF1) -> None

    2. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF2) -> None

    3. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Newmark) -> None

    4. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Bossak) -> None

    5. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.GeneralizedAlpha) -> None
    """
@overload
def CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Newmark) -> None:
    """CalculateMeshVelocities(*args, **kwargs)
    Overloaded function.

    1. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF1) -> None

    2. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF2) -> None

    3. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Newmark) -> None

    4. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Bossak) -> None

    5. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.GeneralizedAlpha) -> None
    """
@overload
def CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Bossak) -> None:
    """CalculateMeshVelocities(*args, **kwargs)
    Overloaded function.

    1. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF1) -> None

    2. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF2) -> None

    3. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Newmark) -> None

    4. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Bossak) -> None

    5. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.GeneralizedAlpha) -> None
    """
@overload
def CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.GeneralizedAlpha) -> None:
    """CalculateMeshVelocities(*args, **kwargs)
    Overloaded function.

    1. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF1) -> None

    2. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.BDF2) -> None

    3. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Newmark) -> None

    4. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.Bossak) -> None

    5. CalculateMeshVelocities(arg0: Kratos.ModelPart, arg1: Kratos.TimeDiscretization.GeneralizedAlpha) -> None
    """
def MoveMesh(arg0: Kratos.NodesArray) -> None:
    """MoveMesh(arg0: Kratos.NodesArray) -> None"""
@overload
def MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float, arg3: Kratos.Array3, arg4: Kratos.Array3) -> None:
    """MoveModelPart(*args, **kwargs)
    Overloaded function.

    1. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float, arg3: Kratos.Array3, arg4: Kratos.Array3) -> None

    2. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters, arg4: Kratos.Parameters) -> None

    3. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.AffineTransform) -> None

    4. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.ParametricAffineTransform) -> None
    """
@overload
def MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters, arg4: Kratos.Parameters) -> None:
    """MoveModelPart(*args, **kwargs)
    Overloaded function.

    1. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float, arg3: Kratos.Array3, arg4: Kratos.Array3) -> None

    2. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters, arg4: Kratos.Parameters) -> None

    3. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.AffineTransform) -> None

    4. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.ParametricAffineTransform) -> None
    """
@overload
def MoveModelPart(arg0: Kratos.ModelPart, arg1: AffineTransform) -> None:
    """MoveModelPart(*args, **kwargs)
    Overloaded function.

    1. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float, arg3: Kratos.Array3, arg4: Kratos.Array3) -> None

    2. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters, arg4: Kratos.Parameters) -> None

    3. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.AffineTransform) -> None

    4. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.ParametricAffineTransform) -> None
    """
@overload
def MoveModelPart(arg0: Kratos.ModelPart, arg1: ParametricAffineTransform) -> None:
    """MoveModelPart(*args, **kwargs)
    Overloaded function.

    1. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float, arg3: Kratos.Array3, arg4: Kratos.Array3) -> None

    2. MoveModelPart(arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Parameters, arg3: Kratos.Parameters, arg4: Kratos.Parameters) -> None

    3. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.AffineTransform) -> None

    4. MoveModelPart(arg0: Kratos.ModelPart, arg1: KratosMeshMovingApplication.ParametricAffineTransform) -> None
    """
def SuperImposeMeshDisplacement(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
    """SuperImposeMeshDisplacement(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None"""
def SuperImposeMeshVelocity(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
    """SuperImposeMeshVelocity(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None"""
