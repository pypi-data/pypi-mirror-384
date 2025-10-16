The code in the examples directory is a set of scripts that you can run to
trigger Freeplay functionality. We use it internally to validate our service and
make sure the instrumentation is working as expected. The examples may be
helpful if you are are trying to understand how to set up your agent or how to
get your traces to show up in Freeplay as expected.

## Setup

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Fill in your API keys** in the `.env` file:
   - `FREEPLAY_API_URL`, `FREEPLAY_API_KEY`, `FREEPLAY_PROJECT_ID` (required)
   - LLM provider keys (OpenAI, Anthropic, Google - based on your Freeplay prompts)

3. **Install dependencies**:
   ```bash
   uv sync
   ```

## Running Examples
You can run it like so: `uv run pytest examples/test_research_agent.py`.


In the default setup, requests to LLMs are captured via VCR so our tests do not
cost a fortune, but requests to localhost are allowed through, so we can test
against a locally running Freeplay server.
