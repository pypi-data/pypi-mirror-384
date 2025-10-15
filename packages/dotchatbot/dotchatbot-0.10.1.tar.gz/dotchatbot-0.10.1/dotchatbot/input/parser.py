from typing import List
from typing import Literal
from typing import Optional

from lark import Lark

from dotchatbot.input.transformer import Message
from dotchatbot.input.transformer import SectionTransformer

GRAMMAR = """
    start: section+
        | content

    section: header content

    header: "@@>" _WS ROLE _WS "(" MODEL ")" ":" _WS
        | "@@>" _WS ROLE ":" _WS

    ROLE: /[a-zA-Z]+/

    MODEL: /.+(?=\\):\n)/x

    ?content: (line_without_header)*

    line_without_header: MARKDOWN
        | NL

    MARKDOWN: /(?!@@>).+/

    %import common.WS -> _WS
    %import common.NEWLINE -> NL
    """


class Parser:
    def __init__(self) -> None:
        self.lark = Lark(GRAMMAR, parser='lalr')
        self.transformer = SectionTransformer()
        self.last_failed_document: Optional[str] | Literal[False] = False

    def parse(self, document: Optional[str]) -> List[Message]:
        try:
            if not document or not document.strip():
                return []
            tree = self.lark.parse(document.lstrip())
            return self.transformer.transform(tree)
        except Exception as e:
            self.last_failed_document = document.lstrip() if document else None
            raise e
