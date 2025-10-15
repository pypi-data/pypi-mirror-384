from dataclasses import dataclass
from html import escape as html_escape
from typing import Any, Callable, Generic, Never, TypeVar

from hexdoc.minecraft import I18n, LocalizedStr
from jinja2 import pass_context
from jinja2.runtime import Context

T = TypeVar("T")

# Hexdoc lacks support for arguments in lang files.
# This is a tragedy and needs to be corrected.
# ... wait what do you mean 'contribute upstream'?


@dataclass
class I18nTuple(Generic[T]):
    # Passed into %
    res: Callable[["I18nTuple[T]"], str]
    args: tuple[T, ...]

    def resolve(self):
        return self.res(self)

    def resolve_html_oneline(self):
        return html_escape(self.resolve()).replace("\n", "&#10;")

    def __str__(self):
        return self.resolve()

    @staticmethod
    def _get_formatter(text: str):
        def formatter(tup: "I18nTuple[Any]"):
            return text % tup.args

        return formatter

    @classmethod
    def of(cls, ls: LocalizedStr) -> "I18nTuple[Never]":
        return I18nTuple(res=lambda _: ls.value, args=())

    @classmethod
    def ofa(cls, ls: LocalizedStr, args: tuple[Any, ...]) -> "I18nTuple[Any]":
        return I18nTuple(res=cls._get_formatter(ls.value), args=args)

    @classmethod
    def join(
        cls, joiner: str, contents: list["I18nTuple[Any]"]
    ) -> "I18nTuple[I18nTuple[Any]]":
        return I18nTuple(
            res=lambda t: joiner.join(map(lambda x: x.resolve(), t.args)),
            args=tuple(contents),
        )

    @classmethod
    def untranslated(cls, text: str) -> "I18nTuple[Never]":
        return I18nTuple(res=lambda _: text, args=())


ArglessI18n = I18nTuple[Never]
