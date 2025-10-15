from hexdoc.minecraft import LocalizedStr
from hexdoc.patchouli.page import Page, PageWithText


class PageWithTextAlternate(PageWithText, type="hexcasting:mediatransport/text"):
    # Literally the same as the superclass
    pass


class HtmlPage(Page, type="hexcasting:mediatransport/hexdoc/html"):
    content: LocalizedStr


class BeginAltnMarker(Page, type="hexcasting:mediatransport/hexdoc/begin_altn"):
    pass


class EndAltnMarker(Page, type="hexcasting:mediatransport/hexdoc/end_altn"):
    pass


# Literally nothing


class ParityPage(Page, type="hexcasting:mediatransport/hexdoc/parity"):
    pass


class ProtocolDocsPage(Page, type="hexcasting:mediatransport/virtual/protocoldocs"):
    pass


class APIDocsPage(Page, type="hexcasting:mediatransport/virtual/apidocs"):
    pass


class NullPage(PageWithText, type="hexcasting:mediatransport/hexdoc/null"):
    pass


class ChannelsPage(Page, type="hexcasting:mediatransport/hexdoc/channels"):
    pass


# API!
class ProtocolSection(Page, type="mediatransport:protocol_section"):
    sections: list[str]
