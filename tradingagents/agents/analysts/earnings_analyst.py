from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.earnings_tools import (
    get_earnings_calendar,
    get_earnings_history,
    get_earnings_surprises,
    get_eps_revisions,
)
from tradingagents.dataflows.config import get_config


def create_earnings_analyst(llm):
    def earnings_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_earnings_calendar,
            get_earnings_history,
            get_earnings_surprises,
            get_eps_revisions,
        ]

        system_message = (
            "You are an earnings analyst tasked with analyzing a company's earnings data. "
            "Use the available tools to fetch upcoming earnings dates, historical quarterly results, "
            "earnings surprise data, and analyst EPS revision trends. "
            "Analyze the company's earnings history to identify patterns in beats and misses. "
            "Assess the magnitude and consistency of earnings surprises over recent quarters. "
            "Evaluate analyst revision momentum — are estimates being revised upward or downward, "
            "and how has the pace of revisions changed over 7-day, 30-day, 60-day, and 90-day windows? "
            "Provide a forward-looking earnings outlook incorporating upcoming earnings dates, "
            "consensus estimates, and whether revision trends suggest the street is becoming more "
            "optimistic or pessimistic. Write a comprehensive earnings briefing with specific "
            "implications for the stock's near-term trajectory."
            + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "earnings_report": report,
        }

    return earnings_analyst_node
