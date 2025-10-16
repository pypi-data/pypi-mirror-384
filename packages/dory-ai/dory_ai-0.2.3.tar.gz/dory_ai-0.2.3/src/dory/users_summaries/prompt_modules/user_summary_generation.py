from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from .types import PromptModel, UserSummaryGenerationInput, UserSummaryGenerationOutput

__all__ = [
    "USER_SUMMARY_GENERATION_PROMPT",
    "create_user_summary_agent",
    "ainvoke_user_summary_generation",
]


USER_SUMMARY_GENERATION_PROMPT = PromptModel(
    prompt_name="user_summary_generation",
    model="gpt-4-turbo-preview",
    json_format=True,
    temperature=0.3,
    template="""
<context>
You are an expert at analyzing conversations and creating comprehensive user summaries.
Your purpose is to extract meaningful information about users from their conversations
and actions, creating summaries that help provide personalized experiences.
</context>

<instructions>
1. Analyze the provided conversation messages and user actions
2. If an existing summary exists, update it with new information
3. Extract structured metadata about the user including:
   - Personal information (name, occupation, location if mentioned)
   - Preferences and interests
   - Behavioral patterns
   - Goals or intentions
   - Context about their situation
4. Identify key topics discussed or acted upon
5. Create a concise, human-readable summary
6. Assign a confidence score based on information quality
</instructions>

<input_data>
{input_data}
</input_data>

<rules>
- Only include information explicitly stated or clearly implied
- Preserve all important details from existing summary when updating
- Use clear, professional language in the summary
- Structure metadata as a nested dictionary with meaningful keys
- Confidence score should reflect the amount and quality of information
- Do not make assumptions beyond what's in the data
- Focus on information relevant for personalization
</rules>

Generate a comprehensive user summary following this structure:
{format_instructions}
""",
)


def create_user_summary_agent(
    api_key: str | None = None,
) -> Agent[UserSummaryGenerationInput, UserSummaryGenerationOutput]:
    model = OpenAIChatModel(USER_SUMMARY_GENERATION_PROMPT.model)

    return Agent(
        model=model,
        output_type=UserSummaryGenerationOutput,
        system_prompt=USER_SUMMARY_GENERATION_PROMPT.template,
    )


async def ainvoke_user_summary_generation(
    input_data: UserSummaryGenerationInput,
    agent: Agent[UserSummaryGenerationInput, UserSummaryGenerationOutput],
) -> UserSummaryGenerationOutput:
    formatted_input = {
        "existing_summary": input_data.existing_summary or "No existing summary",
        "conversation_messages": "\n".join(input_data.conversation_messages),
        "user_actions": "\n".join(input_data.user_actions)
        if input_data.user_actions
        else "No recent actions",
    }

    result = await agent.run(
        USER_SUMMARY_GENERATION_PROMPT.template.format(
            input_data=formatted_input,
            format_instructions="Provide the output as a JSON object with the required fields.",
        )
    )

    return result.output
