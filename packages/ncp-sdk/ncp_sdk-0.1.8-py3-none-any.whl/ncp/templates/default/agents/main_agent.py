"""Main agent definition."""

from ncp import Agent, tool, LLMConfig


@tool
def hello_world(name: str = "World") -> str:
    """Say hello to someone.

    Args:
        name: Name of the person to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


# Define your agent
agent = Agent(
    name="{{ project_name }}Agent",
    description="A helpful AI assistant",
    instructions="""
    You are a helpful AI assistant. Your goal is to assist users with their tasks.

    Be:
    - Concise and clear in your responses
    - Helpful and friendly
    - Professional

    Use the available tools to accomplish tasks when appropriate.
    """,
    tools=[hello_world],
    llm_config=LLMConfig(
        temperature=0.7,
        max_tokens=1500
    )
)
