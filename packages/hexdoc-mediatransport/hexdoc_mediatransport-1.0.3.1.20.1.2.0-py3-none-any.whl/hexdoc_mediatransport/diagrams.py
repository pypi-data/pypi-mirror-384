# Block diagrams and other protocol helpers.

import re
from types import SimpleNamespace
from typing import Callable, Literal, NamedTuple, Protocol

from hexdoc.minecraft import I18n
from jinja2 import pass_context
from jinja2.runtime import Context
from markupsafe import Markup

from .api import Plural, ResolvedSymbol
from .lang import I18nTuple

BOOK = "mediatransport.book"

symbols: dict[str, ResolvedSymbol] = {}
plurals: dict[str, Plural] = {}


@pass_context
def plural(ctx: Context, key: str, amount: int) -> I18nTuple[int]:
    return plurals[key].get(ctx, amount)


@pass_context
def plural_var(ctx: Context, key: str, amount: str) -> I18nTuple[str]:
    return plurals[key].get_var(ctx, amount)


@pass_context
def sym_name(ctx: Context, word: str) -> str:
    symbol = symbols[word]
    return symbol.render_name(ctx).resolve()


@pass_context
def symdef(ctx: Context, id: str, aka: str | None = None) -> str:
    symbol = symbols[id]
    inner = aka if aka is not None else symbol.render_name(ctx).resolve()
    return (
        f'<span class="protocol-sym-def" id="mediatransport-protocol-{id}">'
        f"{inner}"
        "</span>"
    )


@pass_context
def anchor(ctx: Context, id: str, aka: str | None = None) -> str:
    del ctx, aka

    if id not in symbols:
        raise KeyError(f"Unknown symbol ID: {id}")
    return f'<span id="mediatransport-protcol-{id}"></span>'


@pass_context
def symr(ctx: Context, id: str, aka: str | None = None) -> str:
    symbol = symbols[id]
    inner = aka if aka is not None else symbol.render_name(ctx).resolve()
    return f'<span class="protocol-sym-raw">{inner}</span>'


@pass_context
def sym(ctx: Context, id: str, aka: str | None = None) -> str:
    symbol = symbols[id]
    inner = aka if aka is not None else symbol.render_name(ctx).resolve()
    return f'<a class="protocol-sym" href="#mediatransport-protocol-{id}">{inner}</a>'


class _symfn(Protocol):
    def __call__(self, ctx: Context, id: str, aka: str | None = None) -> str: ...


tags: dict[str, _symfn] = {"symdef": symdef, "sym": sym, "symr": symr, "anchor": anchor}


# {sym:id}
# {symdef:id}
# {symr:id}
# {sym:id:alias}
matching_pattern = re.compile(r"{(sym(?:|def|r)|anchor):(\w+)(?::([^}:]+))?}")


def _make_matcher(context: Context):
    def _handle_match(match: re.Match[str]) -> str:
        tag, value, aka = match.groups()
        return tags[tag](context, value, aka)

    return _handle_match


def process_markup(context: Context, raw: str) -> Markup:
    return Markup(matching_pattern.sub(_make_matcher(context), raw))


class Block(NamedTuple):
    size: int | tuple[str, str] | None
    kind: Literal["literal", "sym"]
    sym: str


@pass_context
def dia(context: Context, blocks: list[Block]) -> Markup:
    block_template = context.environment.get_template("block_diagram.html.jinja")
    new_ctx = context.get_all().copy()
    new_ctx["blocks"] = blocks
    return Markup(block_template.render(new_ctx))


class _Box(SimpleNamespace):
    # you can setattr on it I guess
    tl: Callable[[Context, str], Markup]
    dia: Callable[[Context, list[Block]], Markup]
    sym: _symfn
    sym_name: Callable[[Context, str], str]
    codeblock: Callable[[Context, str], Markup]
    plural: Callable[[Context, str, int], I18nTuple[int]]
    plural_var: Callable[[Context, str, str], I18nTuple[str]]


def context(base: str):
    @pass_context
    def tl(context: Context, key: str) -> Markup:
        i18n = I18n.of(context)
        translated = i18n.localize(f"{base}.{key}").value
        return process_markup(context, translated)

    @pass_context
    def codeblock(context: Context, key: str) -> Markup:
        i18n = I18n.of(context)
        raw = i18n.localize(f"{base}.{key}").value
        raw = re.sub(r"^\.", "", raw, flags=re.MULTILINE)
        return Markup(f"<pre>\n{raw}\n</pre>")

    Box = _Box()
    Box.tl = tl
    Box.dia = dia
    Box.sym = sym
    Box.sym_name = sym_name

    Box.codeblock = codeblock

    Box.plural = plural
    Box.plural_var = plural_var

    return Box
