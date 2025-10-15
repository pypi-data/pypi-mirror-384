from rich.console import Console
from rich.console import JustifyMethod
from rich.markdown import Markdown
from typing import Optional

from dotchatbot.input.transformer import Message


class Renderer:
    def __init__(
        self,
        markdown_justify: JustifyMethod,
        markdown_code_theme: str,
        markdown_hyperlinks: bool,
        markdown_inline_code_lexer: str | None = None,
        markdown_inline_code_theme: str | None = None,
        markdown_max_width: Optional[int] = None,
    ) -> None:
        self.get_markdown = lambda output: Markdown(
            output,
            justify=markdown_justify,
            code_theme=markdown_code_theme,
            hyperlinks=markdown_hyperlinks,
            inline_code_lexer=markdown_inline_code_lexer,
            inline_code_theme=markdown_inline_code_theme
        )
        self.console = Console(width=markdown_max_width)

    def render(self, message: Message) -> str:
        content = f'# {message.model}\n{message.content}'
        markdown = self.get_markdown(content)
        with self.console.capture() as capture:
            self.console.print(markdown)
        return capture.get()
