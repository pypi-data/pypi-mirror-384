## OpenAI Agents Example

This example demonstrates how to use the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) to connect to the [MQTT MCP server](https://github.com/ezhuk/mqtt-mcp) using the Streamable HTTP transport.

## Getting Started

Run the following command to install `uv` or check out the [installation guide](https://docs.astral.sh/uv/getting-started/installation/) for more details and alternative installation methods.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repository, then use `uv` to install project dependencies and create a virtual environment.

```bash
git clone https://github.com/ezhuk/mqtt-mcp.git
cd mqtt-mcp/examples/openai-agents
uv sync
```

Start the MQTT MCP server in a separate terminal window and leave it running.

```bash
uv run mqtt-mcp
```

Make sure the `OPENAI_API_KEY` environment variable is set and run the example.

```bash
uv run main.py
```

You should see the output similar to the following.

```text
Running: Publish {"foo":"bar"} to topic "devices/foo" on 127.0.0.1:1883.
Publish to "devices/foo" on 127.0.0.1:1883 has succedeed.
Running: Receive a message from topic "devices/bar", waiting up to 30 seconds.
Received {"bar":123} published to "devices/bar".
```

Modify the prompts in the `run` function depending on the target MQTT device.
