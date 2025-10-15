from dataclasses import dataclass
from typing import Protocol, final

import pluggy
from hexdoc.minecraft import I18n
from jinja2 import pass_context
from jinja2.runtime import Context

from .lang import ArglessI18n, I18nTuple

PLUGGY_NS = "mediatransport"


hookspec = pluggy.HookspecMarker(PLUGGY_NS)


@dataclass
class ExtensionSection:
    id: str
    """Unique identifying name for this section."""
    template: str
    """
    Location of the template to render, for example `mediatransport:filename.html.jinja`.
    """
    ordering: int
    """
    Numbering specifying render order. Not necessarily related to iota type IDs.
    
    Here's what the built in types use:
    - `0`   - Hex Casting
    - `10`  - MoreIotas
    - `20`  - Hexpose
    - `100` - Specials
    """


@dataclass
class Symbol:
    id: str
    """
    Unique identifier that can be used in `{sym:}`-type markup.
    """

    translate: str
    """
    Translation key fragment for this symbol.

    The full translation key is based on your addon's *symbol path*.
    """


@dataclass
class ResolvedSymbol(Symbol):
    root: str
    """
    Symbol root key for this symbol. Should be automatically assigned
    when registered.
    """

    def render_name(self, ctx: Context) -> ArglessI18n:
        i18n = I18n.of(ctx)
        return I18nTuple.of(i18n.localize(f"{self.root}.{self.translate}"))


@dataclass
class Plural:
    key: str

    @pass_context
    def get(self, ctx: Context, amount: int) -> I18nTuple[int]:
        i18n = I18n.of(ctx)
        match amount:
            case 0:
                return I18nTuple.ofa(
                    i18n.localize(f"{self.key}.0", self.key), (amount,)
                )
            case 1:
                return I18nTuple.ofa(
                    i18n.localize(f"{self.key}.1", self.key), (amount,)
                )
            case _:
                return I18nTuple.ofa(i18n.localize(self.key), (amount,))

    @pass_context
    def get_var(self, ctx: Context, text: str) -> I18nTuple[str]:
        i18n = I18n.of(ctx)
        return I18nTuple.ofa(i18n.localize(self.key), (text,))


class MediaTransportExtension:
    """
    It's not a 'plugin' because the class named `MediaTransportPlugin` is a hexdoc plugin

    Anwyay, extend this, and in `__init__`:
    - call the superclass: `super().__init__("YOUR_EXTENSION_ID")`
    - define `self.symbol_root_key`
    - define `self.plural_root_key` if you have pluralizations
    - call methods as needed to register all the things
    """

    id: str
    """
    Your mod / extension ID.
    Is configured by super.__init__.
    """

    symbol_root_key: str
    """
    The base path to your symbol translations.

    Should not end with trailing dot; example: `mediatransport.book.symbols`
    """

    plural_root_key: str | None
    """
    The base path to your pluralizations.

    Should not end with trailing dot; example: `mediatransport.book.pluralizations`.

    Pluralizations should have:
    - the root key, for 'many'
    - optional `.0` key, for 'none'
    - optional `.1` key, for 'one'
    """

    _sections: dict[str, ExtensionSection]
    _symbols: dict[str, Symbol]
    _plurals: set[str]

    def __init__(self, id: str) -> None:
        self._sections = {}
        self._symbols = {}
        self._plurals = set()
        self.plural_root_key = None
        self.id = id

    @final
    def register_section(self, section: ExtensionSection):
        """
        Register an extension section to the documentation.
        """
        if section.id in self._sections:
            raise ValueError(f"Registering section with duplicate id '{section.id}'")
        self._sections[section.id] = section

    @final
    def register_symbol(self, symbol: Symbol):
        """
        Register a symbol to your extension's symbol root.
        """
        if symbol.id in self._symbols:
            raise ValueError(f"Registering symbol with duplicate id '{symbol.id}'")
        self._symbols[symbol.id] = symbol

    @final
    def create_symbol(self, id: str, translate: str):
        """
        Register a symbol from ID and translation key.
        """
        self.register_symbol(Symbol(id=id, translate=translate))

    @final
    def create_symbols(self, mapping: dict[str, str]):
        """
        Register symbols in bulk.
        """
        for id, translate in mapping.items():
            self.create_symbol(id, translate)

    @final
    def register_plural(self, key: str):
        """
        Register a plural to your extension's pluralization root.
        """
        if self.plural_root_key is None:
            raise ValueError(
                "No pluralization root defined for this extension! (self.plural_root_key)"
            )
        self._plurals.add(key)

    @final
    def get_sections(self) -> list[ExtensionSection]:
        return list(self._sections.values())

    @final
    def get_symbols(self) -> dict[str, ResolvedSymbol]:
        return {
            k: ResolvedSymbol(v.id, v.translate, self.symbol_root_key)
            for k, v in self._symbols.items()
        }

    @final
    def get_plurals(self) -> dict[str, Plural]:
        if len(self._plurals) == 0:
            return {}
        if self.plural_root_key is None:
            raise ValueError(
                "No pluralization root defined for this extension! (self.plural_root_key)"
            )
        return {k: Plural(f"{self.plural_root_key}.{k}") for k in self._plurals}


class MediaTransportPlugSpec(Protocol):
    @staticmethod
    @hookspec
    def mediatransport() -> list[MediaTransportExtension]:
        """
        Return an instance of your extension class.
        """
        ...


class MediaTransportPlugImpl(Protocol):
    """Implementation of a mediatransport extension.

    Technically optional, but helps with types and autocomplete and all that.
    """

    @staticmethod
    def mediatransport() -> MediaTransportExtension:
        """
        Return an instance of your extension class.
        """
        ...
