#! /usr/bin/env python3

import asyncio
import os
from typing import cast

from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from payloop import Payloop

if os.environ.get("PAYLOOP_TEST_MODE", None) != "1":
    raise RuntimeError("PAYLOOP_TEST_MODE is not set")

if os.environ.get("OPENAI_API_KEY", None) is None:
    raise RuntimeError("OPENAI_API_KEY is not set")

PROMPT_LABELER_PROMPT = """
You are a precise AI agent specializing in prompt classification and labeling.

## Task
Analyze the provided prompt and assign ONE descriptive label that captures its primary intent/objective.

## Label Requirements
- Use title case formatting
- Words separated by spaces (no camelCase)
- Abbreviations permitted when clear
- Focus on the main action/purpose and domain
- Be specific yet concise

## Output
- Label: <domain> <role> <purpose> (four words maximum, separated by space)
- Reason: The reason for the label (concise sentence, no more than 2 sentences)

Examples on how to label the prompt:
<examples>
    <example>
        <prompt>You are a Python expert. Help users write clean, efficient Python code, debug issues, and follow best practices. Provide detailed explanations and examples.</prompt>
        <label>Python Code Expert</label>
        <reason>The prompt establishes a Python programming expert role focused on code quality, debugging, and best practices. This captures the technical domain and advisory purpose.</reason>
    </example>
    <example>
        <prompt>You are a business analyst. Analyze market trends, competitive landscapes, financial data, and provide strategic recommendations for business growth.</prompt>
        <label>Business Strategy Analyst</label>
        <reason>The prompt defines a business analyst role with focus on market analysis and strategic recommendations. This reflects the analytical function within the business domain.</reason>
    </example>
    <example>
        <prompt>You are a research assistant. Help gather information, analyze sources, organize findings, and support academic or professional research projects.</prompt>
        <label>Research Support Assistant</label>
        <reason>The prompt creates a research assistant role for information gathering and analysis support. This emphasizes the supportive function in academic/professional research contexts.</reason>
    </example>
    <example>
        <prompt>You are a creative writing coach. Guide writers through storytelling techniques, character development, plot structure, and help improve their narrative skills.</prompt>
        <label>Creative Writing Coach</label>
        <reason>The prompt establishes a coaching role specifically for creative writing instruction and skill development. This captures both the educational approach and creative domain focus.</reason>
    </example>
</examples>
"""


class ConversationLabel(BaseModel):
    """
    Represents the result of labeling a conversation.
    """

    name: str = Field(..., description="The assigned label name for the conversation")
    reasoning: str = Field(..., description="The reasoning behind the label assignment")


class SystemPromptLabeler:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def ainvoke(self, prompt: str) -> ConversationLabel:
        messages = [
            SystemMessage(content=PROMPT_LABELER_PROMPT),
            HumanMessage("Here is the prompt: <prompt>" + prompt + "</prompt>"),
        ]

        result = await self.llm.with_structured_output(ConversationLabel).ainvoke(
            messages
        )
        return cast(ConversationLabel, result)


async def main():
    llm = ChatOpenAI(model="gpt-4.1-mini")

    Payloop(
        api_key="Ba2ghufk9YncYhywqQLyAPFq9kGScSLUi1xZ4A66nVyqWlJBVGZJRWGNHeCgBeCHOkgTXWsQH1YMchknyMusYpfR02eyE2JTEKlIm-oTCFPx24yn563Aucb88kMI98ABVXyhse02Fz8i9qrG1UzAalLmYPrpRUS03SCb7AV4wsw"
    ).langchain.register(chatopenai=llm)

    labeler = SystemPromptLabeler(llm)
    result = await labeler.ainvoke(
        "You are a helpful assistant that helps users with coding questions."
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
