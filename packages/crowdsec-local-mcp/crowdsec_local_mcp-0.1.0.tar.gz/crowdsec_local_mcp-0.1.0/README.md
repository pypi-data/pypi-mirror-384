<p align="center">
<img src="https://github.com/crowdsecurity/crowdsec-docs/blob/main/crowdsec-docs/static/img/crowdsec_logo.png" alt="CrowdSec" title="CrowdSec" width="400" height="260"/>
</p>


**Life is too short to write YAML, just ask nicely!**

> A Model Context Protocol (MCP) server to generate, validate, and deploy CrowdSec WAF rules & Scenarios.


## Features

### WAF Rules Features

- **WAF Rule Generation**: Generate CrowdSec WAF rules from user input or a CVE reference
- **Validation**: Validate syntaxical correctness of WAF rules
- **Linting**: Get warnings and hints to improve your WAF rules
- **Deployment Guide**: Step-by-step deployment instructions
- **Docker Test Harness**: Spin up CrowdSec + nginx + bouncer to exercise rules for false positives/negatives
- **Nuclei Lookup**: Quickly jump to existing templates in the official `projectdiscovery/nuclei-templates` repository for a given CVE

### Scenarios Features

- **CrowdSec Scenarios Generation**: Generate CrowdSec scenarios
- **Validation**: Validate syntaxical correctness of scenarios
- **Linting**: Get warnings and hints to improve your scenarios
- **Deployment Guide**: Step-by-step deployment instructions
- **Docker Test Harness**: Spin up CrowdSec to test scenario behavior

## Demo

### WAF Rules Creation and testing

 - [Rule creation from natural language with Claude Desktop](https://claude.ai/share/f0f246b2-6b20-4d70-a16c-c6b627ab2d80)
 - [Rule creation from CVE reference](https://claude.ai/share/b6599407-82dd-443c-a12d-9a9825ed99df)

### Scenario Creation and testing

 - XX
 - XX

## Installation

### Setup

Install dependencies using `uv`:
```bash
uv sync
```

## Configuration for Claude Desktop

### macOS/Linux

1. Find your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the MCP server configuration:
```json
{
  "mcpServers": {
    "crowdsec-prompt-server": {
      "command": "/path/to/crowdsec-mcp-rule-helper/.venv/bin/python",
      "args": [
        "/path/to/crowdsec-mcp-rule-helper/mcp-prompt.py"
      ],
      "cwd": "/path/to/crowdsec-mcp-rule-helper"
    }
  }
}
```

**Important**: Replace `/path/to/crowdsec-mcp-rule-helper` with the actual absolute path to your cloned repository.

## Pre Requisites

 - Docker + Docker Compose

 - Python
