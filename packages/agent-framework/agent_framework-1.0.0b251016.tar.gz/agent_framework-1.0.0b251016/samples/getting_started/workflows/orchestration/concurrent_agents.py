# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Any

from agent_framework import ChatMessage, ConcurrentBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

"""
Sample: Concurrent fan-out/fan-in (agent-only API) with default aggregator

Build a high-level concurrent workflow using ConcurrentBuilder and three domain agents.
The default dispatcher fans out the same user prompt to all agents in parallel.
The default aggregator fans in their results and yields output containing
a list[ChatMessage] representing the concatenated conversations from all agents.

Demonstrates:
- Minimal wiring with ConcurrentBuilder().participants([...]).build()
- Fan-out to multiple agents, fan-in aggregation of final ChatMessages
- Workflow completion when idle with no pending work

Prerequisites:
- Azure OpenAI access configured for AzureOpenAIChatClient (use az login + env vars)
- Familiarity with Workflow events (AgentRunEvent, WorkflowOutputEvent)
"""


async def main() -> None:
    # 1) Create three domain agents using AzureOpenAIChatClient
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    researcher = chat_client.create_agent(
        instructions=(
            "You're an expert market and product researcher. Given a prompt, provide concise, factual insights,"
            " opportunities, and risks."
        ),
        name="researcher",
    )

    marketer = chat_client.create_agent(
        instructions=(
            "You're a creative marketing strategist. Craft compelling value propositions and target messaging"
            " aligned to the prompt."
        ),
        name="marketer",
    )

    legal = chat_client.create_agent(
        instructions=(
            "You're a cautious legal/compliance reviewer. Highlight constraints, disclaimers, and policy concerns"
            " based on the prompt."
        ),
        name="legal",
    )

    # 2) Build a concurrent workflow
    # Participants are either Agents (type of AgentProtocol) or Executors
    workflow = ConcurrentBuilder().participants([researcher, marketer, legal]).build()

    # 3) Run with a single prompt and pretty-print the final combined messages
    events = await workflow.run("We are launching a new budget-friendly electric bike for urban commuters.")
    outputs = events.get_outputs()

    if outputs:
        print("===== Final Aggregated Conversation (messages) =====")
        for output in outputs:
            messages: list[ChatMessage] | Any = output
            for i, msg in enumerate(messages, start=1):
                name = msg.author_name if msg.author_name else "user"
                print(f"{'-' * 60}\n\n{i:02d} [{name}]:\n{msg.text}")

    """
    Sample Output:

    ===== Final Aggregated Conversation (messages) =====
    ------------------------------------------------------------

    01 [user]:
    We are launching a new budget-friendly electric bike for urban commuters.
    ------------------------------------------------------------

    02 [researcher]:
    **Insights:**

    - **Target Demographic:** Urban commuters seeking affordable, eco-friendly transport;
        likely to include students, young professionals, and price-sensitive urban residents.
    - **Market Trends:** E-bike sales are growing globally, with increasing urbanization,
        higher fuel costs, and sustainability concerns driving adoption.
    - **Competitive Landscape:** Key competitors include brands like Rad Power Bikes, Aventon,
        Lectric, and domestic budget-focused manufacturers in North America, Europe, and Asia.
    - **Feature Expectations:** Customers expect reliability, ease-of-use, theft protection,
        lightweight design, sufficient battery range for daily city commutes (typically 25-40 miles),
        and low-maintenance components.

    **Opportunities:**

    - **First-time Buyers:** Capture newcomers to e-biking by emphasizing affordability, ease of
        operation, and cost savings vs. public transit/car ownership.
    ...
    ------------------------------------------------------------

    03 [marketer]:
    **Value Proposition:**
    "Empowering your city commute: Our new electric bike combines affordability, reliability, and
        sustainable design—helping you conquer urban journeys without breaking the bank."

    **Target Messaging:**

    *For Young Professionals:*
    ...
    ------------------------------------------------------------

    04 [legal]:
    **Constraints, Disclaimers, & Policy Concerns for Launching a Budget-Friendly Electric Bike for Urban Commuters:**

    **1. Regulatory Compliance**
    - Verify that the electric bike meets all applicable federal, state, and local regulations
        regarding e-bike classification, speed limits, power output, and safety features.
    - Ensure necessary certifications (e.g., UL certification for batteries, CE markings if sold internationally) are obtained.

    **2. Product Safety**
    - Include consumer safety warnings regarding use, battery handling, charging protocols, and age restrictions.
    ...
    """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
