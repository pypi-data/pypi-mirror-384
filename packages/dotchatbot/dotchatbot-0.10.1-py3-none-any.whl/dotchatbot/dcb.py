import asyncio
import os
import sys
from asyncio import TaskGroup
from datetime import datetime
from getpass import getpass
from os.path import abspath
from typing import get_args
from typing import Iterable
from typing import List
from typing import Optional

import click
import keyring
import lark
from click import Choice
from click import UsageError
from click._termui_impl import Editor
from click_extra import ColorOption
from click_extra import ConfigOption
from click_extra import extra_command
from click_extra import ShowParamsOption
from click_extra import VerboseOption
from click_extra import VerbosityOption
from cloup import option
from cloup import option_group
from rich.console import JustifyMethod

from dotchatbot.client.factory import create_client
from dotchatbot.client.factory import ServiceName
from dotchatbot.client.services import ServiceClient
from dotchatbot.input.parser import Parser
from dotchatbot.input.transformer import Message
from dotchatbot.output.file import generate_file_content
from dotchatbot.output.file import generate_filename
from dotchatbot.output.file import NEW_USER_MESSAGE
from dotchatbot.output.markdown import Renderer

APP_NAME = "dotchatbot"
os.makedirs(click.get_app_dir(APP_NAME), exist_ok=True)

DEFAULT_SYSTEM_PROMPT = """\
You are a helpful assistant."""

DEFAULT_SUMMARY_PROMPT = """\
Given the conversation so far, summarize it in just 4 words. \
Only respond with these 4 words"""

DEFAULT_QUICK_PROMPT = """You are a queryable information engine that returns \
a max of 5 bullet-points. Do not respond with a summary. \
Only respond with a list of bullet-points. Be succinct and use less bullet \
points when possible. Include examples."""

DEFAULT_SESSION_HISTORY_FILE = os.path.join(
    click.get_app_dir(APP_NAME), ".dotchatbot-history"
)
DEFAULT_SESSION_FILE_LOCATION = os.path.join(
    click.get_app_dir(APP_NAME), "sessions", datetime.now().date().isoformat()
)
os.makedirs(DEFAULT_SESSION_FILE_LOCATION, exist_ok=True)
DEFAULT_SESSION_FILE_EXT = ".dcb"


def _edit(text: str, extension: str, reverse: bool) -> Optional[str]:
    editor = Editor().get_editor()
    if editor in ("vim", "vi"):
        line_offset = 2 if reverse else ""
        editor += f" +{line_offset}"
    file_content = click.edit(
        editor=editor,
        text=text,
        extension=extension,
    )
    return file_content


async def _create_client(
    service_name: ServiceName,
    system_prompt: str,
    openai_model: str,
    anthropic_model: str,
    anthropic_max_tokens: int,
    google_model: str,
) -> ServiceClient:
    api_key = await asyncio.to_thread(
        keyring.get_password,
        service_name.lower(),
        "api_key"
    )
    if not api_key:
        api_key = getpass(f"Enter your {service_name} API key: ")
        keyring.set_password(service_name.lower(), "api_key", api_key)

    return create_client(
        service_name=service_name,
        system_prompt=system_prompt,
        api_key=api_key,
        openai_model=openai_model,
        anthropic_model=anthropic_model,
        anthropic_max_tokens=anthropic_max_tokens,
        google_model=google_model,
    )


def _print_history(session_history_file: str) -> None:
    with open(session_history_file, "r") as f:
        previous = ''
        for line in f:
            filename = line.strip()
            if os.path.exists(filename):
                mtime = os.path.getmtime(filename)
                mtime = datetime.fromtimestamp(mtime)
                if previous != filename:
                    click.echo(f"{mtime} {filename}")
                    previous = filename


def _print_response(
    no_rich: bool,
    no_pager: bool,
    chatbot_responses: List[Message],
    markdown_renderer: Renderer
) -> None:
    output = ""
    for chatbot_response in chatbot_responses:
        if no_rich or not sys.stdout.isatty():
            output += chatbot_response.content
        else:
            output += markdown_renderer.render(chatbot_response)

    if no_pager or not sys.stdout.isatty():
        click.echo(output)
    else:
        click.echo(output)
        click.echo_via_pager(output, color=True)


@extra_command(
    params=[
        ConfigOption(strict=True),
        ShowParamsOption(),
        ColorOption(),
        VerbosityOption(),
        VerboseOption(),
    ]
)
@click.argument("filename", required=False)
@option_group(
    "Options", option(
        "--system-prompt",
        "-p",
        help="The default system prompt to use",
        default=DEFAULT_SYSTEM_PROMPT
    ), option(
        "--no-pager",
        is_flag=True,
        help="Do not output using pager",
        default=False
    ), option(
        "--no-rich",
        is_flag=True,
        help="Do not output using rich",
        default=False
    ), option(
        "--reverse",
        "-r",
        help="Reverse the conversation in the editor",
        is_flag=True,
        default=False
    ), option(
        "--assume-yes", "-y", help='''\
Automatic yes to prompts; \
assume "yes" as answer to all prompts and run non-interactively.\
''', is_flag=True, default=False
    ), option(
        "--assume-no", "-n", help='''\
Automatic no to prompts; \
assume "no" as answer to all prompts and run non-interactively.\
''', is_flag=True, default=False
    ), option(
        "--current-directory",
        "-c",
        help="Use the current directory as the session file location",
        is_flag=True,
        default=False
    ), option(
        "--session-history-file",
        help="The file where the session history is stored",
        default=DEFAULT_SESSION_HISTORY_FILE,
        show_default=False
    ), option(
        "--session-file-location",
        help="The location where session files are stored",
        default=DEFAULT_SESSION_FILE_LOCATION,
        show_default=False
    ), option(
        "--session-file-ext",
        help="The extension to use for session files",
        default=DEFAULT_SESSION_FILE_EXT
    ), option(
        "--summary-prompt", help="""\
The prompt to use for the summary (for building the filename for the session)\
""", default=DEFAULT_SUMMARY_PROMPT
    ), option(
        "--service-name",
        "-s",
        help="The chatbot provider service name",
        default="OpenAI",
        type=click.Choice(get_args(ServiceName))
    ), option(
        "--summary-service-name",
        help="The chatbot provider service name for filename generation",
        default="OpenAI",
        type=click.Choice(get_args(ServiceName))
    ), option(
        "--quick-service-name",
        help="Call this model first, then the main model.",
        default=None
    ), option(
        "--quick-system-prompt",
        help="System prompt for the quick response model",
        default=DEFAULT_QUICK_PROMPT
    ), option(
        "--history",
        "-H",
        help="Print history of sessions",
        is_flag=True,
        default=False
    )
)
@option_group(
    "OpenAI options", option(
        "--openai-model", default="gpt-4o"
    ), option(
        "--quick-openai-model", default="gpt-4o"
    ), option(
        "--summary-openai-model", default="gpt-4o"
    )
)
@option_group(
    "Anthropic options", option(
        "--anthropic-model", default="claude-3-7-sonnet-latest"
    ), option(
        "--quick-anthropic-model", default="claude-3-sonnet-latest"
    ), option(
        "--summary-anthropic-model", default="claude-3-sonnet-latest"
    ), option(
        "--anthropic-max-tokens", default=16384, type=int
    )
)
@option_group(
    "Google options", option(
        "--google-model", default="gemini-2.5-pro"
    ), option(
        "--quick-google-model", default="gemini-2.5-flash-lite"
    ), option(
        "--summary-google-model", default="gemini-2.5-flash-lite"
    )
)
@option_group(
    "Markdown options",
    option(
        "--markdown-justify",
        default="default",
        type=click.Choice(get_args(JustifyMethod))
    ),
    option("--markdown-code-theme", default="monokai"),
    option("--markdown-hyperlinks", is_flag=True, default=False),
    option("--markdown-inline-code-lexer"),
    option("--markdown-inline-code-theme"),
    option(
        "--markdown-max-width",
        type=int,
        default=125,
        help="Maximum width of the output"
    )
)
def dotchatbot(
    filename: Optional[str],
    system_prompt: str,
    no_pager: bool,
    no_rich: bool,
    reverse: bool,
    assume_yes: bool,
    assume_no: bool,
    current_directory: bool,
    session_history_file: str,
    session_file_location: str,
    session_file_ext: str,
    summary_prompt: str,
    history: bool,
    service_name: ServiceName,
    summary_service_name: ServiceName,
    quick_service_name: Optional[ServiceName],
    quick_system_prompt: str,
    openai_model: str,
    summary_openai_model: str,
    quick_openai_model: str,
    anthropic_model: str,
    summary_anthropic_model: str,
    quick_anthropic_model: str,
    anthropic_max_tokens: int,
    google_model: str,
    summary_google_model: str,
    quick_google_model: str,
    markdown_justify: JustifyMethod,
    markdown_code_theme: str,
    markdown_hyperlinks: bool,
    markdown_inline_code_lexer: str,
    markdown_inline_code_theme: str,
    markdown_max_width: Optional[int] = None
) -> None:
    """
    Starts a session with the chatbot, resume by providing FILENAME.
    Provide - for FILENAME to use the previous session
    (stored in SESSION_HISTORY_FILE).
    """
    keyring.core.init_backend()

    if history:
        _print_history(session_history_file)
        return

    if assume_yes and assume_no:
        raise UsageError("--assume-yes and --assume-no are mutually exclusive")

    prompt_user = not assume_no and not assume_yes

    if sys.stdin.isatty() and not sys.stdout.isatty():
        raise UsageError("STDOUT must not be TTY when STDIN is TTY")

    if not sys.stdin.isatty() and prompt_user:
        raise UsageError("Must use -y or -n when STDIN is not TTY")

    if filename == "-":
        if os.path.exists(session_history_file):
            with open(session_history_file, "r") as f:
                lines = f.readlines()
                if lines:
                    filename = lines[-1].strip()
                    click.echo(
                        f"Resuming from previous session: {filename}",
                        file=sys.stderr
                    )
                else:
                    filename = None
        else:
            filename = None

    parser = Parser()

    async def _run() -> None:
        def _get_next_message(
            _messages: List[Message]
        ) -> List[Message]:
            if sys.stdin.isatty():
                if not reverse:
                    file_content = generate_file_content(_messages)
                    text = f"{file_content}{NEW_USER_MESSAGE}"
                    file_content = _edit(
                        text=text,
                        extension=session_file_ext,
                        reverse=reverse
                    )
                    _messages = parser.parse(file_content)
                else:
                    reversed_messages_from_file = list(reversed(_messages))
                    file_content = generate_file_content(
                        reversed_messages_from_file)
                    text = f"{NEW_USER_MESSAGE}{file_content}"
                    file_content = _edit(
                        text=text,
                        extension=session_file_ext,
                        reverse=reverse
                    )
                    _messages = list(reversed(parser.parse(file_content)))
            else:
                _messages = [*_messages, *parser.parse(sys.stdin.read())]
            return _messages

        init_messages: List[Message] = []
        if filename and os.path.exists(filename):
            with open(filename, "r") as f:
                init_messages = parser.parse(f.read())

        init_messages = _get_next_message(init_messages)

        async with TaskGroup() as tg:
            client_task = tg.create_task(_create_client(
                service_name=service_name,
                system_prompt=system_prompt,
                openai_model=openai_model,
                anthropic_model=anthropic_model,
                anthropic_max_tokens=anthropic_max_tokens,
                google_model=google_model,
            ))
            summary_client_task = tg.create_task(_create_client(
                service_name=summary_service_name,
                system_prompt=system_prompt,
                openai_model=summary_openai_model,
                anthropic_model=summary_anthropic_model,
                anthropic_max_tokens=anthropic_max_tokens,
                google_model=summary_google_model,
            ))
            quick_client_task = tg.create_task(_create_client(
                service_name=quick_service_name,
                system_prompt=quick_system_prompt,
                openai_model=quick_openai_model,
                anthropic_model=quick_anthropic_model,
                anthropic_max_tokens=anthropic_max_tokens,
                google_model=quick_google_model,
            )) if quick_service_name else None

        client = client_task.result()
        summary_client = summary_client_task.result()
        quick_client = quick_client_task.result() \
            if quick_client_task else None

        markdown_renderer = Renderer(
            markdown_justify,
            markdown_code_theme,
            markdown_hyperlinks,
            markdown_inline_code_lexer,
            markdown_inline_code_theme,
            markdown_max_width
        )

        async def _get_responses(_messages: List[Message]) -> List[Message]:
            chatbot_response = asyncio.create_task(
                client.create_chat_completion(
                    _messages
                )
            )

            chatbot_responses = []
            if quick_client:
                quick_chatbot_response = asyncio.create_task(
                    quick_client.create_chat_completion(
                        _messages
                    )
                )

                done, pending = await asyncio.wait(
                    [quick_chatbot_response, chatbot_response],
                    return_when=asyncio.FIRST_COMPLETED
                )
                if quick_chatbot_response in done:
                    chatbot_responses.append(quick_chatbot_response.result())
                    _print_response(
                        no_rich,
                        True,
                        chatbot_responses,
                        markdown_renderer
                    )
                else:
                    quick_chatbot_response.cancel()

            await chatbot_response
            chatbot_responses.append(chatbot_response.result())

            _print_response(
                no_rich,
                no_pager,
                chatbot_responses,
                markdown_renderer
            )
            return chatbot_responses

        save_file_task: Optional[asyncio.Task[str]] = None

        async def _loop(messages: Iterable[Message]) -> None:
            nonlocal save_file_task
            prompt = True
            _filename = filename
            _messages: List[Message] = list(messages)
            while prompt:
                is_empty_message = (
                    not _messages
                    or not _messages[-1].content.strip()
                    or _messages[-1].role != "user"
                )
                if is_empty_message:
                    raise UsageError("Aborting request due to empty message")

                _messages = [*_messages, *(await _get_responses(_messages))]

                async def _generate_filename(
                    _filename: str | None,
                    _messages: List[Message],
                ) -> str:
                    if _filename:
                        return _filename
                    generated_filename = await generate_filename(
                        summary_client, summary_prompt, _messages,
                        session_file_ext
                    )
                    if current_directory:
                        return os.path.join(os.curdir, generated_filename)
                    else:
                        return os.path.join(
                            session_file_location,
                            generated_filename
                        )
                _filename_task = asyncio.create_task(_generate_filename(
                    _filename,
                    _messages,
                ))

                if prompt_user:
                    result = click.prompt(
                        "Save response?",
                        default="Y",
                        type=Choice(["y", "n", "c"], case_sensitive=False),
                        show_choices=True
                    )
                    save = result.lower() in ("y", "yes", "c")
                    prompt = result.lower() == "c"
                elif assume_yes:
                    save = True
                    prompt = False
                else:
                    save = False
                    prompt = False

                if save:
                    async def _save_file(
                        _messages: List[Message],
                        _filename_task: asyncio.Task[str],
                    ) -> str:
                        generated_filename = await _filename_task
                        with open(generated_filename, "w") as f:
                            f.write(generate_file_content(_messages))
                            session_file_absolute_path = abspath(f.name)

                        open(session_history_file, "a").write(
                            session_file_absolute_path + "\n"
                        )
                        click.echo(
                            f"Saved to {generated_filename}",
                            file=sys.stderr
                        )
                        return generated_filename
                    if save_file_task is not None:
                        _filename = await save_file_task

                    save_file_task = asyncio.create_task(_save_file(
                        _messages,
                        _filename_task
                    ))

                if prompt:
                    _messages = _get_next_message(_messages)
            if save_file_task and not save_file_task.done():
                await save_file_task

        try:
            await _loop(init_messages)
        finally:
            if save_file_task is not None and not save_file_task.done():
                await save_file_task

    try:
        asyncio.run(_run())
    except lark.exceptions.UnexpectedInput as e:
        if isinstance(parser.last_failed_document, str):
            raise UsageError(f"""\
{str(e)}
{e.get_context(parser.last_failed_document, span=120)}\
""")
        else:
            raise e


if __name__ == "__main__":
    dotchatbot(auto_envvar_prefix="DOTCHATBOT", prog_name=APP_NAME)
