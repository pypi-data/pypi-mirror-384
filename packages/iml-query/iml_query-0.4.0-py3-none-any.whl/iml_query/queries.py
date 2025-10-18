"""Query source strings and definitions for IML tree-sitter queries."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Self, override

from tree_sitter import Node


@dataclass(frozen=True)
class BaseCapture:
    @classmethod
    def from_ts_capture(cls, capture: dict[str, list[Node]]) -> Self:
        """Create a new instance of the class from tree-sitter capture dict.

        Args:
            capture (dict[str, list[Node]]): Tree-sitter capture dict.
                keys are the capture names, values are lists of nodes (normally
                of length 1).

        """
        capture_: dict[str, Node] = {k: v[0] for k, v in capture.items()}

        field_names = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in capture_.items() if k in field_names}
        return cls(**filtered)


VERIFY_QUERY_SRC = r"""
(verify_statement) @verify
"""


@dataclass(slots=True, frozen=True)
class VerifyCapture(BaseCapture):
    verify: Node


INSTANCE_QUERY_SRC = r"""
(instance_statement) @instance
"""


@dataclass(slots=True, frozen=True)
class InstanceCapture(BaseCapture):
    instance: Node


AXIOM_QUERY_SRC = r"""
(axiom_definition) @axiom
"""

THEOREM_QUERY_SRC = r"""
(theorem_definition) @theorem
"""

LEMMA_QUERY_SRC = r"""
(lemma_definition) @lemma
"""

DECOMP_QUERY_SRC = r"""
(value_definition
    (let_binding
        (value_name) @decomposed_func_name
        (item_attribute
            (attribute_id) @_decomp_id
            (attribute_payload) @decomp_payload
            (#eq? @_decomp_id "decomp")
        ) @decomp_attr
    )
)
"""


@dataclass(slots=True, frozen=True)
class DecompCapture(BaseCapture):
    decomposed_func_name: Node
    decomp_attr: Node
    decomp_payload: Node


EVAL_QUERY_SRC = r"""
(eval_statement) @eval
"""


@dataclass(slots=True, frozen=True)
class EvalCapture(BaseCapture):
    eval: Node


# TODO:
# (path import with explicit module name)
# [@@@import Mod_name, "path/to/file.iml"]
# (same, with explicit extraction name)
# [@@@import Mod_name, "path/to/file.iml", Mod_name2]
# (path import as module `File`)
# [@@@import "path/to/file.iml"]
# (import from ocamlfind library)
# [@@@import Mod_name, "findlib:foo.bar"]
# (same, with explicit extraction name)
# [@@@import Mod_name, "findlib:foo.bar", Mod_name2]
# (import from dune library)
# [@@@import Mod_name, "dune:foo.bar"]
# (same, with explicit extraction name)
# [@@@import Mod_name, "dune:foo.bar", Mod_name2]

GENERAL_IMPORT_QUERY_SRC = r"""
(floating_attribute
    "[@@@"
    (attribute_id) @attribute_id
    (#eq? @attribute_id "import")
) @import
"""

IMPORT_1_QUERY_SRC = r"""
(floating_attribute
    "[@@@"
    (attribute_id) @attribute_id
    (#eq? @attribute_id "import")
    (attribute_payload
        (expression_item
            (tuple_expression
                (constructor_path
                    (constructor_name) @import_name
                )
                (string
                    (string_content) @import_path
                )
            )
        )
    )
) @import
"""

IMPORT_3_QUERY_SRC = r"""
(floating_attribute
    "[@@@"
    (attribute_id) @attribute_id
    (#eq? @attribute_id "import")
    (attribute_payload
        (expression_item
            (string
                (string_content) @import_path
            )
        )
    )
) @import
"""

VALUE_DEFINITION_QUERY_SRC = r"""
(value_definition
    "rec"? @rec
    (let_binding
        (value_name) @function_name
    )
) @function_definition
"""


@dataclass(slots=True, frozen=True)
class ValueDefCapture(BaseCapture):
    function_definition: Node
    function_name: Node
    is_rec: bool
    is_top_level: bool

    @override
    @classmethod
    def from_ts_capture(cls, capture: dict[str, list[Node]]) -> Self:
        data: dict[str, Node | bool] = {}
        func_def_node = capture['function_definition'][0]
        data['function_definition'] = func_def_node
        data['function_name'] = capture['function_name'][0]
        data['is_rec'] = 'rec' in capture
        assert func_def_node.parent, 'Never: no parent'
        parent_type = func_def_node.parent.type
        data['is_top_level'] = parent_type == 'compilation_unit'
        return cls(**data)  # pyright: ignore


MEASURE_QUERY_SRC = r"""
(value_definition
    (let_binding
        pattern: (value_name) @function_name
        (item_attribute
            "[@@"
            (attribute_id) @_measure_id
            (#eq? @_measure_id "measure")
        ) @measure_attr
    )
) @function_definition
"""


@dataclass(slots=True, frozen=True)
class MeasureCapture(BaseCapture):
    function_definition: Node
    function_name: Node
    measure_attr: Node


OPAQUE_QUERY_SRC = r"""
(value_definition
    (let_binding
        (value_name) @function_name
        (item_attribute
            (attribute_id) @_opaque_id
            (#eq? @_opaque_id "opaque")
        ) @opaque_attr
    )
) @function_definition
"""


@dataclass(slots=True, frozen=True)
class OpaqueCapture(BaseCapture):
    function_definition: Node
    function_name: Node
    opaque_attr: Node
