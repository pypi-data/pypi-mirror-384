# Copyright (c) Microsoft. All rights reserved.

import asyncio
from random import randint
from typing import Annotated

from agent_framework import AgentThread, ChatAgent
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from pydantic import Field

"""
Azure OpenAI Responses Client with Thread Management Example

This sample demonstrates thread management with Azure OpenAI Responses Client, comparing
automatic thread creation with explicit thread management for persistent context.
"""


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def example_with_automatic_thread_creation() -> None:
    """Example showing automatic thread creation."""
    print("=== Automatic Thread Creation Example ===")

    # For authentication, run `az login` command in terminal or replace AzureCliCredential with preferred
    # authentication option.
    agent = ChatAgent(
        chat_client=AzureOpenAIResponsesClient(credential=AzureCliCredential()),
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # First conversation - no thread provided, will be created automatically
    query1 = "What's the weather like in Seattle?"
    print(f"User: {query1}")
    result1 = await agent.run(query1)
    print(f"Agent: {result1.text}")

    # Second conversation - still no thread provided, will create another new thread
    query2 = "What was the last city I asked about?"
    print(f"\nUser: {query2}")
    result2 = await agent.run(query2)
    print(f"Agent: {result2.text}")
    print("Note: Each call creates a separate thread, so the agent doesn't remember previous context.\n")


async def example_with_thread_persistence_in_memory() -> None:
    """
    Example showing thread persistence across multiple conversations.
    In this example, messages are stored in-memory.
    """
    print("=== Thread Persistence Example (In-Memory) ===")

    # For authentication, run `az login` command in terminal or replace AzureCliCredential with preferred
    # authentication option.
    agent = ChatAgent(
        chat_client=AzureOpenAIResponsesClient(credential=AzureCliCredential()),
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # Create a new thread that will be reused
    thread = agent.get_new_thread()

    # First conversation
    query1 = "What's the weather like in Tokyo?"
    print(f"User: {query1}")
    result1 = await agent.run(query1, thread=thread)
    print(f"Agent: {result1.text}")

    # Second conversation using the same thread - maintains context
    query2 = "How about London?"
    print(f"\nUser: {query2}")
    result2 = await agent.run(query2, thread=thread)
    print(f"Agent: {result2.text}")

    # Third conversation - agent should remember both previous cities
    query3 = "Which of the cities I asked about has better weather?"
    print(f"\nUser: {query3}")
    result3 = await agent.run(query3, thread=thread)
    print(f"Agent: {result3.text}")
    print("Note: The agent remembers context from previous messages in the same thread.\n")


async def example_with_existing_thread_id() -> None:
    """
    Example showing how to work with an existing thread ID from the service.
    In this example, messages are stored on the server using Azure OpenAI conversation state.
    """
    print("=== Existing Thread ID Example ===")

    # First, create a conversation and capture the thread ID
    existing_thread_id = None

    # For authentication, run `az login` command in terminal or replace AzureCliCredential with preferred
    # authentication option.
    agent = ChatAgent(
        chat_client=AzureOpenAIResponsesClient(credential=AzureCliCredential()),
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # Start a conversation and get the thread ID
    thread = agent.get_new_thread()

    query1 = "What's the weather in Paris?"
    print(f"User: {query1}")
    # Enable Azure OpenAI conversation state by setting `store` parameter to True
    result1 = await agent.run(query1, thread=thread, store=True)
    print(f"Agent: {result1.text}")

    # The thread ID is set after the first response
    existing_thread_id = thread.service_thread_id
    print(f"Thread ID: {existing_thread_id}")

    if existing_thread_id:
        print("\n--- Continuing with the same thread ID in a new agent instance ---")

        agent = ChatAgent(
            chat_client=AzureOpenAIResponsesClient(credential=AzureCliCredential()),
            instructions="You are a helpful weather agent.",
            tools=get_weather,
        )

        # Create a thread with the existing ID
        thread = AgentThread(service_thread_id=existing_thread_id)

        query2 = "What was the last city I asked about?"
        print(f"User: {query2}")
        result2 = await agent.run(query2, thread=thread, store=True)
        print(f"Agent: {result2.text}")
        print("Note: The agent continues the conversation from the previous thread by using thread ID.\n")


async def main() -> None:
    print("=== Azure OpenAI Response Client Agent Thread Management Examples ===\n")

    await example_with_automatic_thread_creation()
    await example_with_thread_persistence_in_memory()
    await example_with_existing_thread_id()


if __name__ == "__main__":
    asyncio.run(main())
