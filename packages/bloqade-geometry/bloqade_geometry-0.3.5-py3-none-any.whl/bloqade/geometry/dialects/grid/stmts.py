from kirin import ir, lowering, types
from kirin.decl import info, statement
from kirin.dialects import ilist

from ._dialect import dialect
from .types import GridType

FloatTupleType = types.Tuple[types.Vararg(types.Float)]


@statement(dialect=dialect)
class FromPositions(ir.Statement):
    name = "from_positions"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    x_positions: ir.SSAValue = info.argument(
        type=ilist.IListType[types.Float, NumX := types.TypeVar("NumX")]
    )
    y_positions: ir.SSAValue = info.argument(
        type=ilist.IListType[types.Float, NumY := types.TypeVar("NumY")]
    )
    result: ir.ResultValue = info.result(GridType[NumX, NumY])


@statement(dialect=dialect)
class FromRanges(ir.Statement):
    name = "from_ranges"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})

    x_start: ir.SSAValue = info.argument(types.Int)
    x_stop: ir.SSAValue = info.argument(types.Int)
    x_step: ir.SSAValue = info.argument(types.Int)
    y_start: ir.SSAValue = info.argument(types.Int)
    y_stop: ir.SSAValue = info.argument(types.Int)
    y_step: ir.SSAValue = info.argument(types.Int)


@statement(dialect=dialect)
class New(ir.Statement):
    name = "new"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})

    x_spacing: ir.SSAValue = info.argument(
        type=ilist.IListType[types.Float, types.TypeVar("NumXStep")]
    )
    y_spacing: ir.SSAValue = info.argument(
        type=ilist.IListType[types.Float, types.TypeVar("NumYStep")]
    )
    x_init: ir.SSAValue = info.argument(types.Float)
    y_init: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(
        GridType[types.TypeVar("NumX"), types.TypeVar("NumY")]
    )


@statement(dialect=dialect)
class Positions(ir.Statement):
    name = "positions"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])
    result: ir.ResultValue = info.result(
        ilist.IListType[types.Tuple[types.Float, types.Float], types.Any]
    )


# Maybe do this with hints?
@statement(dialect=dialect)
class Shape(ir.Statement):
    name = "shape"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])
    result: ir.ResultValue = info.result(types.Tuple[types.Int, types.Int])


@statement(dialect=dialect)
class Get(ir.Statement):
    name = "get"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(type=GridType)
    idx: ir.SSAValue = info.argument(types.Tuple[types.Int, types.Int])
    result: ir.ResultValue = info.result(types.Tuple[types.Float, types.Float])


@statement(dialect=dialect)
class GetXPos(ir.Statement):
    name = "get.xpos"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[NumX := types.TypeVar("NumX"), types.Any]
    )
    result: ir.ResultValue = info.result(ilist.IListType[types.Float, NumX])


@statement(dialect=dialect)
class GetYPos(ir.Statement):
    name = "get.ypos"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[types.Any, NumY := types.TypeVar("NumY")]
    )
    result: ir.ResultValue = info.result(ilist.IListType[types.Float, NumY])


@statement(dialect=dialect)
class GetSubGrid(ir.Statement):
    name = "get_sub_grid"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])
    x_indices: ir.SSAValue = info.argument(
        ilist.IListType[types.Int, GetNumX := types.TypeVar("GetNumX")]
    )
    y_indices: ir.SSAValue = info.argument(
        ilist.IListType[types.Int, GetNumY := types.TypeVar("GetNumY")]
    )
    result: ir.ResultValue = info.result(GridType[GetNumX, GetNumY])


@statement(dialect=dialect)
class GetXBounds(ir.Statement):
    name = "get_x_bounds"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[NumXBounds := types.TypeVar("NumXBounds"), types.Any]
    )
    result: ir.ResultValue = info.result(types.Tuple[types.Float, types.Float])


@statement(dialect=dialect)
class GetYBounds(ir.Statement):
    name = "get_y_bounds"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[types.Any, NumYBounds := types.TypeVar("NumYBounds")]
    )
    result: ir.ResultValue = info.result(types.Tuple[types.Float, types.Float])


@statement(dialect=dialect)
class Shift(ir.Statement):
    name = "shift_grid"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[NumX := types.TypeVar("NumX"), NumY := types.TypeVar("NumY")]
    )
    x_shift: ir.SSAValue = info.argument(types.Float)
    y_shift: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(GridType[NumX, NumY])


@statement(dialect=dialect)
class ShiftSubgridX(ir.Statement):
    name = "shift_subgrid_x"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[NumX := types.TypeVar("NumX"), NumY := types.TypeVar("NumY")]
    )
    x_indices: ir.SSAValue = info.argument(
        ilist.IListType[types.Int, types.TypeVar("SubNumX")]
    )
    x_shift: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(GridType[NumX, NumY])


@statement(dialect=dialect)
class ShiftSubgridY(ir.Statement):
    name = "shift_subgrid_y"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[NumX := types.TypeVar("NumX"), NumY := types.TypeVar("NumY")]
    )
    y_indices: ir.SSAValue = info.argument(
        ilist.IListType[types.Int, types.TypeVar("SubNumY")]
    )
    y_shift: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(GridType[NumX, NumY])


@statement(dialect=dialect)
class Scale(ir.Statement):
    name = "scale_grid"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(
        type=GridType[NumX := types.TypeVar("NumX"), NumY := types.TypeVar("NumY")]
    )
    x_scale: ir.SSAValue = info.argument(types.Float)
    y_scale: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(GridType[NumX, NumY])


@statement(dialect=dialect)
class Repeat(ir.Statement):
    name = "repeat"

    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})

    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])
    x_times: ir.SSAValue = info.argument(types.Int)
    y_times: ir.SSAValue = info.argument(types.Int)
    x_gap: ir.SSAValue = info.argument(types.Float)
    y_gap: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(GridType[types.Any, types.Any])
