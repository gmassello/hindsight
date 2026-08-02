import os
from typing import Any

import boto3

from hindsight.config import settings
from hindsight.llm.base import Message, ToolSpec, ToolUse, Turn

BEARER_TOKEN_ENV = "AWS_BEARER_TOKEN_BEDROCK"


def _credentials() -> dict[str, str]:
    if not (settings.aws_access_key_id and settings.aws_secret_access_key):
        return {}
    creds = {
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        creds["aws_session_token"] = settings.aws_session_token
    return creds


def _client():
    if settings.bedrock_api_key:
        os.environ.setdefault(BEARER_TOKEN_ENV, settings.bedrock_api_key)
    return boto3.client("bedrock-runtime", region_name=settings.aws_region, **_credentials())


def _to_bedrock_message(message: Message) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    if message.text:
        content.append({"text": message.text})
    for use in message.tool_uses:
        content.append({"toolUse": {"toolUseId": use.id, "name": use.name, "input": use.args}})
    for result in message.tool_results:
        content.append(
            {
                "toolResult": {
                    "toolUseId": result.id,
                    "content": [{"json": {"result": result.content}}],
                    "status": "error" if result.is_error else "success",
                }
            }
        )
    return {"role": message.role, "content": content}


class BedrockClaudeProvider:
    def __init__(self) -> None:
        self.client = _client()
        self.model_id = settings.bedrock_model_id

    def converse(
        self, system: str, messages: list[Message], tools: list[ToolSpec]
    ) -> Turn:
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[_to_bedrock_message(m) for m in messages],
            inferenceConfig={"maxTokens": settings.max_tokens},
            toolConfig={
                "tools": [
                    {
                        "toolSpec": {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": {"json": tool.input_schema},
                        }
                    }
                    for tool in tools
                ]
            },
        )
        turn = Turn(truncated=response.get("stopReason") == "max_tokens")
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                turn.text += block["text"]
            elif "toolUse" in block:
                use = block["toolUse"]
                turn.tool_uses.append(
                    ToolUse(id=use["toolUseId"], name=use["name"], args=use["input"])
                )
        return turn
