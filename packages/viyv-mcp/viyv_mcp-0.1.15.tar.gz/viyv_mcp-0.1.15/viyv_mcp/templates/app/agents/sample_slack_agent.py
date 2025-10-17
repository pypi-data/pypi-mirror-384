from typing import Annotated

from pydantic import Field
from viyv_mcp import agent
from viyv_mcp.openai_bridge import build_function_tools
# import os, json, logging, openai

# from agents import Runner, enable_verbose_stdout_logging

# # ---- ログ設定 --------------------------
# enable_verbose_stdout_logging()  # SDK の内部ログ
# openai.log = "debug"  # HTTP リクエスト／レスポンス全文
# logging.basicConfig(level=logging.DEBUG)


@agent(
    name="slack_agent",
    description="slack を操作するエージェントです。指示に従いslack を操作します。必ず指示を与えてください。",
    use_tags=["slack"],
)
async def slack_agent(
    action_japanese: Annotated[
        str,
        Field(
            title="実行するSlackアクション",
            description="具体的に何をするのかを日本語で指示してください。例：slack チャンネル一覧の取得、スレッドに返信、過去のスレッド履歴を取得...etc.",
        ),
    ],
    instruction: Annotated[
        str, Field(title="Slack操作の指示を具体的に日本語で、指示してください。")
    ],
) -> str:

    # --- ② OpenAI Agents SDK の Tool に変換 -------------------------------
    oa_tools = build_function_tools(exclude_tools=["slack_reply_to_thread"])

    # --- ③ エージェント定義 ----------------------------------------------
    try:
        from agents import Agent as OAAgent, Runner
    except ImportError:
        return "Agents SDK がインストールされていません (`pip install openai-agents-python`)"

    agent_ = OAAgent(
        name="SlackAgent",
        instructions=(
            "あなたは、指示に従い、slack ワークスペースを操作する AI アシスタントです。",
            "",
        ),
        model="o4-mini-2025-04-16",
        tools=oa_tools,
    )

    # --- ④ 実行 ----------------------------------------------------------
    try:
        result = await Runner.run(agent_, f"アクション：{action_japanese} 指示：{instruction}")
        return str(result.final_output)
    except Exception as exc:
        return f"ChatGPT への問い合わせでエラーが発生しました: {exc}"
