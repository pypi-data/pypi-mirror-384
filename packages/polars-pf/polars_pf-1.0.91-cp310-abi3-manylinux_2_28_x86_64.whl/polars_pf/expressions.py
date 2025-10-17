from pathlib import Path
from typing import Optional

import polars as pl
from polars.plugins import register_plugin_function

PLUGIN_PATH: Path = Path(__file__).parent


@pl.api.register_expr_namespace("pfexpr")
class PFramesExpressionsNamespace:
    def __init__(self, expr: pl.Expr) -> None:
        self._expr = expr

    def matches_ecma_regex(
        self,
        ecma_regex: str,
    ) -> pl.Expr:
        """
        Takes Utf8 as input and returns Boolean indicating if the input value
        matches the provided ECMAScript regular expression.
        """
        return register_plugin_function(
            plugin_path=PLUGIN_PATH,
            function_name="matches_ecma_regex",
            args=self._expr,
            kwargs={
                "regex": ecma_regex,
            },
            is_elementwise=True,
        )

    def contains_fuzzy_match(
        self,
        reference: str,
        max_edits: int,
        wildcard: Optional[str] = None,
        substitutions_only: Optional[bool] = None,
    ) -> pl.Expr:
        """
        Takes Utf8 as input and returns Boolean indicating if the input value
        contains close match to provided reference.
        """
        return register_plugin_function(
            plugin_path=PLUGIN_PATH,
            function_name="contains_fuzzy_match",
            args=self._expr,
            kwargs={
                "reference": reference,
                "max_edits": max_edits,
                "wildcard": wildcard,
                "substitutions_only": substitutions_only,
            },
            is_elementwise=True,
        )


class Expr(pl.Expr):
    @property
    def pfexpr(self) -> PFramesExpressionsNamespace:
        return PFramesExpressionsNamespace(self)
