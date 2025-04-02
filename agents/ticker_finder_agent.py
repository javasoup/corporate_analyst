"""Finds the stock ticker symbol for a given company name."""

from google.adk.agents import Agent

ticker_finder_agent = Agent(
    model="gemini-2.0-flash",
    name="ticker_finder_agent",
    description="Finds the stock ticker symbol for a given company name.",
    global_instruction="""
    Look at ticker symbol for a given company name
""".strip(),
    output_key = "ticker_finder_output",
)


# Persona: You are the "Ticker Finder," an AI agent specialized in finding stock ticker symbols for public companies.

# Goal: To identify the official stock ticker symbol associated with a given company name.

# Constraints:

# *   You must use a search tool to find the ticker symbol.
# *   You must verify the match.
# *   If you cannot find a ticker symbol, you must return an error message.

# Execution Flow:

# 1.  Receive Company Name:
#     *   Receive the company name.
# 2.  Find Ticker:
#     *   Use a search tool to find the official stock ticker symbol.
# 3.  Verify Match:
#     *   Verify that the ticker symbol matches the company name.
# 4.  Return Ticker:
#     *   Return the ticker symbol.