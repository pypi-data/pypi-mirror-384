from typing import List, Optional, Union

from msgspec import Struct

from .spec import PTableColumnId


class SingleValueIsNAPredicate(
    Struct, rename="camel", tag_field="operator", tag="IsNA"
):
    pass


class SingleValueEqualPredicate(
    Struct, rename="camel", tag_field="operator", tag="Equal"
):
    reference: Union[str, int, float]


class SingleValueInSetPredicate(
    Struct, rename="camel", tag_field="operator", tag="InSet"
):
    references: List[Union[str, int, float]]


class SingleValueIEqualPredicate(
    Struct, rename="camel", tag_field="operator", tag="IEqual"
):
    reference: str


class SingleValueLessPredicate(
    Struct, rename="camel", tag_field="operator", tag="Less"
):
    reference: Union[str, int, float]


class SingleValueLessOrEqualPredicate(
    Struct, rename="camel", tag_field="operator", tag="LessOrEqual"
):
    reference: Union[str, int, float]


class SingleValueGreaterPredicate(
    Struct, rename="camel", tag_field="operator", tag="Greater"
):
    reference: Union[str, int, float]


class SingleValueGreaterOrEqualPredicate(
    Struct, rename="camel", tag_field="operator", tag="GreaterOrEqual"
):
    reference: Union[str, int, float]


class SingleValueStringContainsPredicate(
    Struct, rename="camel", tag_field="operator", tag="StringContains"
):
    substring: str


class SingleValueStringIContainsPredicate(
    Struct, rename="camel", tag_field="operator", tag="StringIContains"
):
    substring: str


class SingleValueMatchesPredicate(
    Struct, rename="camel", tag_field="operator", tag="Matches"
):
    regex: str


class SingleValueStringContainsFuzzyPredicate(
    Struct,
    rename="camel",
    tag_field="operator",
    tag="StringContainsFuzzy",
    omit_defaults=True,
):
    reference: str
    max_edits: int
    substitutions_only: Optional[bool] = None
    wildcard: Optional[str] = None


class SingleValueStringIContainsFuzzyPredicate(
    Struct,
    rename="camel",
    tag_field="operator",
    tag="StringIContainsFuzzy",
    omit_defaults=True,
):
    reference: str
    max_edits: int
    substitutions_only: Optional[bool] = None
    wildcard: Optional[str] = None


class SingleValueNotPredicate(Struct, rename="camel", tag_field="operator", tag="Not"):
    operand: "SingleValuePredicate"


class SingleValueAndPredicate(Struct, rename="camel", tag_field="operator", tag="And"):
    operands: List["SingleValuePredicate"]


class SingleValueOrPredicate(Struct, rename="camel", tag_field="operator", tag="Or"):
    operands: List["SingleValuePredicate"]


SingleValuePredicate = Union[
    SingleValueIsNAPredicate,
    SingleValueEqualPredicate,
    SingleValueInSetPredicate,
    SingleValueIEqualPredicate,
    SingleValueLessPredicate,
    SingleValueLessOrEqualPredicate,
    SingleValueGreaterPredicate,
    SingleValueGreaterOrEqualPredicate,
    SingleValueStringContainsPredicate,
    SingleValueStringIContainsPredicate,
    SingleValueMatchesPredicate,
    SingleValueStringContainsFuzzyPredicate,
    SingleValueStringIContainsFuzzyPredicate,
    SingleValueNotPredicate,
    SingleValueAndPredicate,
    SingleValueOrPredicate,
]


class PTableRecordFilter(Struct, rename="camel", tag="bySingleColumnV2"):
    column: PTableColumnId
    predicate: SingleValuePredicate
