from hexdoc_mediatransport import hookimpl

from .api import ExtensionSection, MediaTransportExtension, MediaTransportPlugImpl


class MediaTransportBuiltInExt(MediaTransportExtension):
    def __init__(self) -> None:
        super().__init__("builtins")
        self.symbol_root_key = "mediatransport.book.symbols"
        self.plural_root_key = "mediatransport.book.pluralizations"
        self.create_symbols(
            {
                # Protocol
                "type": "type",
                "data": "data",
                "double_value": "value",
                "dir": "dir",
                "pattern_len": "length",
                "angles": "angles",
                "vec_x": "x",
                "vec_y": "y",
                "vec_z": "z",
                "list_len": "length",
                "list_iotas": "iotas",
                "str_len": "length",
                "string": "string",
                "rows": "rows",
                "cols": "cols",
                "rowscols": "rowscols",
                "matrix_contents": "contents",
                "protocol_version": "version",
                "max_send": "max_send",
                "max_inter_send": "max_inter_send",
                "max_recv": "max_recv",
                "max_power": "max_power",
                "power_regen_rate": "power_regen_rate",
                "inter_cost": "inter_cost",
                # Figura
                "Buffer": "Buffer",
            }
        )
        self.register_plural("byte")  # byte, bytes
        self.register_section(
            ExtensionSection(
                id="hexcasting",
                template="mediatransport:types/hexcasting.html.jinja",
                ordering=0,
            )
        )
        self.register_section(
            ExtensionSection(
                id="moreiotas",
                template="mediatransport:types/moreiotas.html.jinja",
                ordering=10,
            )
        )
        self.register_section(
            ExtensionSection(
                id="hexpose",
                template="mediatransport:types/hexpose.html.jinja",
                ordering=20,
            )
        )
        self.register_section(
            ExtensionSection(
                id="builtin_specials",
                template="mediatransport:types/builtin_specials.html.jinja",
                ordering=100,
            )
        )


class MediaTransportBuiltIn(MediaTransportPlugImpl):
    @staticmethod
    @hookimpl
    def mediatransport() -> MediaTransportBuiltInExt:
        return MediaTransportBuiltInExt()
