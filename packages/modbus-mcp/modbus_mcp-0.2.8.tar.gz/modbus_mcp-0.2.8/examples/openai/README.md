## OpenAI Remote MCP Example

This example demonstrates how to use the [OpenAI Python library](https://github.com/openai/openai-python) to connect to the [Modbus MCP server](https://github.com/ezhuk/modbus-mcp) using the Streamable HTTP transport.

## Getting Started

Run the following command to install `uv` or check out the [installation guide](https://docs.astral.sh/uv/getting-started/installation/) for more details and alternative installation methods.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repository, then use `uv` to install project dependencies and create a virtual environment.

```bash
git clone https://github.com/ezhuk/modbus-mcp.git
cd modbus-mcp/examples/openai
uv sync
```

Make sure the `OPENAI_API_KEY` environment variable is set and run the example.

```bash
uv run main.py
```

You should see the output similar to the following.

```text
Running: Read the content of 40010 on 127.0.0.1:502.
The content of register 40010 on 127.0.0.1:502 is 10.
Running: Write [123, 45, 678] to registers starting at 40011.
The data [123, 45, 678] was successfully written to registers starting at address 40011.
Running: Read the value of 40012 holding register.
The value of the holding register at address 40012 is 45.
```

Modify the prompts in the `main` function depending on the target Modbus device.
