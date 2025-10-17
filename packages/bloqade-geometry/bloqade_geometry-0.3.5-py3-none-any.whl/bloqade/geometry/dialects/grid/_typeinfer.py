from typing import cast

from kirin import types
from kirin.analysis import TypeInference
from kirin.dialects import ilist
from kirin.interp import Frame, MethodTable, impl

from ._dialect import dialect
from .stmts import New
from .types import GridType


@dialect.register(key="typeinfer")
class TypeInferMethods(MethodTable):

    def get_len(self, typ: types.TypeAttribute):
        if (typ := cast(types.Generic, typ)).is_subseteq(
            ilist.IListType
        ) and isinstance(typ.vars[1], types.Literal):
            # assume typ is Generic since it must be if it passes the first check
            # and the second check is to ensure that the length is a literal
            return types.Literal(typ.vars[1].data + 1)

        return types.Any

    @impl(New)
    def inter_new(self, _: TypeInference, frame: Frame[types.TypeAttribute], node: New):
        x_len = self.get_len(frame.get(node.x_spacing))
        y_len = self.get_len(frame.get(node.y_spacing))

        return (GridType[x_len, y_len],)
