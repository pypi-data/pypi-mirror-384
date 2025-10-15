import itertools
from typing import cast

import pluggy

from .__gradle_version__ import FULL_VERSION
from .api import (
    PLUGGY_NS,
    ExtensionSection,
    MediaTransportExtension,
    MediaTransportPlugSpec,
    Plural,
    ResolvedSymbol,
)
from .builtin_extensions import MediaTransportBuiltIn
from .prettylog import info


class MediaTransportPlugins:
    def _report(self):
        sections = self.get_sections()
        symbols = self.get_symbols()
        plurals = self.get_plurals()
        info(
            f"[bold #b080ff]hexdoc-mediatransport {FULL_VERSION}[/]\n"
            f"  [blue][bold]{len(self.extensions)} extension(s)[/] loaded: {', '.join(map(lambda x: x.id, self.extensions))}[/]\n"
            f"  [yellow][bold]{len(sections)} protocol section(s)[/]: {', '.join(map(lambda x: x.id, sections))}[/]\n"
            f"  [green][bold]{len(symbols)} symbol(s)[/]: {', '.join(map(lambda x: x.id, symbols.values()))}[/]\n"
            f"  [red][bold]{len(plurals)} plural set(s)[/]: {', '.join(map(lambda x: x.key, plurals.values()))}[/]\n"
        )

    def __init__(self) -> None:
        self.plugs = pluggy.PluginManager(PLUGGY_NS)
        self.plugs.add_hookspecs(MediaTransportPlugSpec)
        self.entrypoints()

        self.extensions: list[MediaTransportExtension] = self.get_extensions()

        self._report()

    def entrypoints(self):
        self.plugs.load_setuptools_entrypoints(PLUGGY_NS)
        self.plugs.check_pending()
        self.plugs.register(MediaTransportBuiltIn)

    def get_extensions(self) -> list[MediaTransportExtension]:
        hook: MediaTransportPlugSpec = cast(MediaTransportPlugSpec, self.plugs.hook)
        return hook.mediatransport()

    def get_sections(self) -> list[ExtensionSection]:
        return list(
            sorted(
                itertools.chain(*[x.get_sections() for x in self.extensions]),
                key=lambda x: x.ordering,
            )
        )

    def get_symbols(self) -> dict[str, ResolvedSymbol]:
        symbols: dict[str, ResolvedSymbol] = {}
        keys: set[str] = set()

        for x in self.extensions:
            sym = x.get_symbols()
            if intersect := keys & sym.keys():
                raise ValueError(
                    f"Symbol conflict: {intersect} already exist from other extensions, but also registered by {x.__class__.__name__}"
                )
            symbols |= sym
            keys |= sym.keys()

        return symbols

    def get_plurals(self) -> dict[str, Plural]:
        plurals: dict[str, Plural] = {}
        keys: set[str] = set()

        for x in self.extensions:
            pl = x.get_plurals()
            if intersect := keys & pl.keys():
                raise ValueError(
                    f"Pluralization conflict: {intersect} already exist from other extensions, but also registered by {x.__class__.__name__}"
                )
            plurals |= pl
            keys |= pl.keys()

        return plurals
