from dataclasses import dataclass
from typing import Any
from typing import get_args
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import TypeGuard

from lark import Token
from lark import Transformer
from lark import Tree

Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str
    model: Optional[str] = None


def _content_type_guard(items: List[Tree | str]) -> TypeGuard[List[str]]:
    return all(map(lambda item: type(item) is str, items))


def _join(items: List[Tree | str]) -> str:
    if not _content_type_guard(items):
        raise TypeError("Invalid content")
    return "".join(items)


def _section_type_guard(
    items: Any
) -> TypeGuard[List[Tuple[Tuple[Role, Optional[str]], Tree]]]:
    is_section = map(
        lambda item: item[0][0] in get_args(Role) and type(item[1]) is Tree,
        items
    )
    return all(is_section)


class SectionTransformer(Transformer):
    def __init__(self) -> None:
        super().__init__()

    def start(self, items: List) -> List[Message]:
        first_item: Tree = items[0]
        if first_item.data == "content":
            return [Message(role="user", content=_join(first_item.children))]

        items = list(
            map(lambda item: item.children, items)
        )
        if not _section_type_guard(items):
            raise TypeError("Invalid section")
        return [Message(
            role=role, model=model, content=_join(content.children)
        ) for [(role, model), content] in items]

    def header(self, items: List[Token]) -> Tuple[str, Optional[str]]:
        model = [i.value for i in items if i.type == "MODEL"]
        return ([i.value for i in items if i.type == "ROLE"][0],
                model[0] if len(model) == 1 else None)

    def line_without_header(self, items: List[Token]) -> str:
        return items[0].value
