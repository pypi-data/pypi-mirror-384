from typing import Literal

from dotchatbot.client.services import ServiceClient

ServiceName = Literal["OpenAI", "Anthropic", "Google",]


def create_client(
    service_name: ServiceName,
    system_prompt: str,
    api_key: str,
    openai_model: str,
    anthropic_model: str,
    anthropic_max_tokens: int,
    google_model: str,
) -> ServiceClient:
    if service_name == "OpenAI":
        from dotchatbot.client._openai import OpenAI
        return OpenAI(
            api_key=api_key, system_prompt=system_prompt, model=openai_model
        )
    elif service_name == "Anthropic":
        from dotchatbot.client._anthropic import Anthropic
        return Anthropic(
            api_key=api_key,
            system_prompt=system_prompt,
            model=anthropic_model,
            max_tokens=anthropic_max_tokens
        )
    elif service_name == "Google":
        from dotchatbot.client._google import Google
        return Google(
            api_key=api_key,
            system_prompt=system_prompt,
            model=google_model,
        )
    else:
        raise ValueError(f"Invalid service name: {service_name}")
