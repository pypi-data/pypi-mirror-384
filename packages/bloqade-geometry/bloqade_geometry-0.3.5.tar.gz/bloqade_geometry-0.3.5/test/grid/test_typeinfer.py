from typing import Any, Literal

from kirin import types
from kirin.dialects import ilist

from bloqade.geometry import grid
from bloqade.geometry.prelude import geometry


def test_typeinfer():

    @geometry(typeinfer=True)
    def test_1(spacing: ilist.IList[float, Literal[2]]):
        return grid.new(spacing, [1.0, 2.0], 0.0, 0.0)

    assert test_1.return_type.is_subseteq(
        grid.GridType[types.Literal(3), types.Literal(3)]
    )

    @geometry(typeinfer=True)
    def test_2(spacing: ilist.IList[float, Any]):
        return grid.new(spacing, [1.0, 2.0], 0.0, 0.0)

    assert test_2.return_type.is_equal(grid.GridType[types.Any, types.Literal(3)])
