[![Add to Cursor](https://fastmcp.me/badges/cursor_dark.svg)](https://fastmcp.me/MCP/Details/559/bigquery)
[![Add to VS Code](https://fastmcp.me/badges/vscode_dark.svg)](https://fastmcp.me/MCP/Details/559/bigquery)
[![Add to Claude](https://fastmcp.me/badges/claude_dark.svg)](https://fastmcp.me/MCP/Details/559/bigquery)
[![Add to ChatGPT](https://fastmcp.me/badges/chatgpt_dark.svg)](https://fastmcp.me/MCP/Details/559/bigquery)
[![Add to Codex](https://fastmcp.me/badges/codex_dark.svg)](https://fastmcp.me/MCP/Details/559/bigquery)
[![Add to Gemini](https://fastmcp.me/badges/gemini_dark.svg)](https://fastmcp.me/MCP/Details/559/bigquery)

# BigQuery MCP server

[![smithery badge](https://smithery.ai/badge/mcp-server-bigquery)](https://smithery.ai/server/mcp-server-bigquery)

A Model Context Protocol server that provides access to BigQuery. This server enables LLMs to inspect database schemas and execute queries.

## Components

### Tools

The server implements one tool:

- `execute-query`: Executes a SQL query using BigQuery dialect
- `list-tables`: Lists all tables in the BigQuery database
- `describe-table`: Describes the schema of a specific table

## Configuration

The server can be configured either with command line arguments or environment variables.

| Argument     | Environment Variable | Required | Description                                                                                                                                                                                                                                                                                                                                                    |
| ------------ | -------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--project`  | `BIGQUERY_PROJECT`   | Yes      | The GCP project ID.                                                                                                                                                                                                                                                                                                                                            |
| `--location` | `BIGQUERY_LOCATION`  | Yes      | The GCP location (e.g. `europe-west9`).                                                                                                                                                                                                                                                                                                                        |
| `--dataset`  | `BIGQUERY_DATASETS`  | No       | Only take specific BigQuery datasets into consideration. Several datasets can be specified by repeating the argument (e.g. `--dataset my_dataset_1 --dataset my_dataset_2`) or by joining them with a comma in the environment variable (e.g. `BIGQUERY_DATASETS=my_dataset_1,my_dataset_2`). If not provided, all datasets in the project will be considered. |
| `--key-file` | `BIGQUERY_KEY_FILE`  | No       | Path to a service account key file for BigQuery. If not provided, the server will use the default credentials.                                                                                                                                                                                                                                                 |

## Quickstart

### Install

#### Installing via Smithery

To install BigQuery Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/mcp-server-bigquery):

```bash
npx -y @smithery/cli install mcp-server-bigquery --client claude
```

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

##### Development/Unpublished Servers Configuration</summary>

```json
"mcpServers": {
  "bigquery": {
    "command": "uv",
    "args": [
      "--directory",
      "{{PATH_TO_REPO}}",
      "run",
      "mcp-server-bigquery",
      "--project",
      "{{GCP_PROJECT_ID}}",
      "--location",
      "{{GCP_LOCATION}}"
    ]
  }
}
```

##### Published Servers Configuration

```json
"mcpServers": {
  "bigquery": {
    "command": "uvx",
    "args": [
      "mcp-server-bigquery",
      "--project",
      "{{GCP_PROJECT_ID}}",
      "--location",
      "{{GCP_LOCATION}}"
    ]
  }
}
```

Replace `{{PATH_TO_REPO}}`, `{{GCP_PROJECT_ID}}`, and `{{GCP_LOCATION}}` with the appropriate values.

## Development

### Building and Publishing

To prepare the package for distribution:

1. Increase the version number in `pyproject.toml`

2. Sync dependencies and update lockfile:

```bash
uv sync
```

3. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

4. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:

- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory {{PATH_TO_REPO}} run mcp-server-bigquery
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
