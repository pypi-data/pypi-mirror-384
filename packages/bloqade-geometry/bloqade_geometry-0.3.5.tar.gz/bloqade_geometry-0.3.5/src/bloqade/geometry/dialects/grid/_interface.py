import typing

from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import (
    FromPositions,
    Get,
    GetSubGrid,
    GetXBounds,
    GetXPos,
    GetYBounds,
    GetYPos,
    New,
    Positions,
    Repeat,
    Scale,
    Shape,
    Shift,
    ShiftSubgridX,
    ShiftSubgridY,
)
from .types import Grid


@_wraps(New)
def new(
    x_spacing: ilist.IList[float, typing.Any] | list[float],
    y_spacing: ilist.IList[float, typing.Any] | list[float],
    x_init: float,
    y_init: float,
) -> Grid[typing.Any, typing.Any]:
    """
    Create a new grid with the given spacing and initial position.

    Args:
        x_spacing (IList[float] | list[float]): The spacing in the x direction.
        y_spacing (IList[float] | list[float]): The spacing in the y direction.
        x_init (float): The initial position in the x direction.
        y_init (float): The initial position in the y direction.

    Returns:
        Grid: A new grid object.
    """
    ...


Nx = typing.TypeVar("Nx")
Ny = typing.TypeVar("Ny")


@typing.overload
def from_positions(
    x_positions: ilist.IList[float, Nx], y_positions: ilist.IList[float, Ny]
) -> Grid[Nx, Ny]: ...
@typing.overload
def from_positions(
    x_positions: ilist.IList[float, Nx], y_positions: list[float]
) -> Grid[Nx, typing.Any]: ...
@typing.overload
def from_positions(
    x_positions: list[float], y_positions: ilist.IList[float, Ny]
) -> Grid[typing.Any, Ny]: ...
@typing.overload
def from_positions(
    x_positions: list[float], y_positions: list[float]
) -> Grid[typing.Any, typing.Any]: ...
@_wraps(FromPositions)
def from_positions(x_positions, y_positions):
    """Construct a grid from the given x and y positions.

    Args:
        x_positions (IList[float] | list[float]): A list or ilist of floats representing the x-coordinates of grid points.
        y_positions (IList[float] | list[float]): A list or ilist of floats representing the y-coordinates of grid points.

    Returns:
        Grid: a grid object
    """


@_wraps(Get)
def get(grid: Grid, idx: tuple[int, int]) -> tuple[float, float]:
    """Get the coordinate (x, y) of a grid at the given index.

    Args:
        grid (Grid): a grid object
        idx (tuple[int, int]): a tuple of (x, y) indices
    Returns:
        tuple[float, float]: a tuple of (x, y) positions
        tuple[None, None]: if the grid has no initial x or y position
    """
    ...


@_wraps(GetXPos)
def get_xpos(grid: Grid[Nx, typing.Any]) -> ilist.IList[float, Nx]:
    """Get the x positions of a grid.

    Args:
        grid: a grid object
    Returns:
        ilist.IList[float, typing.Any]: a list of x positions
    """
    ...


@_wraps(GetYPos)
def get_ypos(grid: Grid[typing.Any, Ny]) -> ilist.IList[float, Ny]:
    """Get the y positions of a grid.

    Args:
        grid: a grid object
    Returns:
        ilist.IList[float, typing.Any]: a list of y positions
    """
    ...


@typing.overload
def sub_grid(
    grid: Grid, x_indices: ilist.IList[int, Nx], y_indices: ilist.IList[int, Ny]
) -> Grid[Nx, Ny]: ...
@typing.overload
def sub_grid(
    grid: Grid, x_indices: ilist.IList[int, Nx], y_indices: list[int]
) -> Grid[Nx, typing.Any]: ...
@typing.overload
def sub_grid(
    grid: Grid, x_indices: list[int], y_indices: ilist.IList[int, Ny]
) -> Grid[typing.Any, Ny]: ...
@typing.overload
def sub_grid(
    grid: Grid, x_indices: list[int], y_indices: list[int]
) -> Grid[typing.Any, typing.Any]: ...
@_wraps(GetSubGrid)
def sub_grid(grid, x_indices, y_indices):
    """Get a subgrid from the given grid.

    Args:
        grid (Grid): a grid object
        x_indices: a list/ilist of x indices
        y_indices: a list/ilist of y indices
    Returns:
        Grid: a subgrid object
    """
    ...


@_wraps(GetXBounds)
def x_bounds(grid: Grid[typing.Any, typing.Any]) -> tuple[float, float]:
    """Get the x bounds of a grid.

    Args:
        grid (Grid): a grid object
    Returns:
        tuple[float, float]: a tuple of (min_x, max_x)
    """
    ...


@_wraps(GetYBounds)
def y_bounds(grid: Grid[typing.Any, typing.Any]) -> tuple[float, float]:
    """Get the y bounds of a grid.

    Args:
        grid (Grid): a grid object
    Returns:
        tuple[float, float]: a tuple of (min_y, max_y)
        tuple[None, None]: if the grid has no initial y position
    """
    ...


@_wraps(Positions)
def positions(
    grid: Grid[typing.Any, typing.Any],
) -> ilist.IList[tuple[float, float], typing.Any]:
    """Get the positions of a grid as a list of (x, y) tuples.

    Args:
        grid (Grid): a grid object

    Returns:
        ilist.IList[tuple[float, float], typing.Any]: a list of (x, y) tuples representing the positions of the grid points

    """
    ...


@_wraps(Repeat)
def repeat(
    grid: Grid, x_times: int, y_times: int, x_spacing: float, y_spacing: float
) -> Grid:
    """Repeat a grid in the x and y directions.

    Args:
        grid (Grid): a grid object
        x_times (int): number of times to repeat in the x direction
        y_times (int): number of times to repeat in the y direction
        x_spacing (float): spacing in the x direction
        y_spacing (float): spacing in the y direction
    Returns:
        Grid: a new grid object with the repeated pattern
    """
    ...


@_wraps(Scale)
def scale(grid: Grid[Nx, Ny], x_scale: float, y_scale: float) -> Grid[Nx, Ny]:
    """Scale a grid in the x and y directions.

    Args:
        grid (Grid): a grid object
        x_scale (float): scaling factor in the x direction
        y_scale (float): scaling factor in the y direction
    Returns:
        Grid: a new grid object that has been scaled
    """
    ...


@_wraps(Shift)
def shift(grid: Grid[Nx, Ny], x_shift: float, y_shift: float) -> Grid[Nx, Ny]:
    """Shift a grid in the x and y directions.

    Args:
        grid (Grid): a grid object
        x_shift (float): shift in the x direction
        y_shift (float): shift in the y direction
    Returns:
        Grid: a new grid object that has been shifted
    """
    ...


@_wraps(ShiftSubgridX)
def shift_subgrid_x(
    grid: Grid[Nx, Ny], x_indices: ilist.IList[int, typing.Any], x_shift: float
) -> Grid[Nx, Ny]:
    """Shift a sub grid of grid in the x directions.

    Args:
        grid (Grid): a grid object
        x_indices (ilist.IList[int, typing.Any]): a list/ilist of x indices to shift
        x_shift (float): shift in the x direction
    Returns:
        Grid: a new grid object that has been shifted
    """
    ...


@_wraps(ShiftSubgridY)
def shift_subgrid_y(
    grid: Grid[Nx, Ny], y_indices: ilist.IList[int, typing.Any], y_shift: float
) -> Grid[Nx, Ny]:
    """Shift a sub grid of grid in the y directions.

    Args:
        grid (Grid): a grid object
        y_indices (ilist.IList[int, typing.Any]): a list/ilist of y indices to shift
        y_shift (float): shift in the y direction
    Returns:
        Grid: a new grid object that has been shifted
    """
    ...


@_wraps(Shape)
def shape(grid: Grid) -> tuple[int, int]:
    """Get the shape of a grid.

    Args:
        grid (Grid): a grid object
    Returns:
        tuple[int, int]: a tuple of (num_x, num_y)
    """
    ...
