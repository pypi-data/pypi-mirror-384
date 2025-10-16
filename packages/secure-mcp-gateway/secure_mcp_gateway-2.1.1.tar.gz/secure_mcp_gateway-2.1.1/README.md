# Enkrypt AI Secure MCP Gateway

![enkrypt-secure-mcp-gateway-hld](./docs/images/enkrypt-secure-mcp-gateway-hld.png)

> **📖 Featured Blog Post:** Learn how the Secure MCP Gateway prevents top attacks and vulnerabilities in our latest blog:
>
> **[How Enkrypt's Secure MCP Gateway and MCP Scanner Prevent Top Attacks](https://www.enkryptai.com/blog/how-enkrypts-secure-mcp-gateway-and-mcp-scanner-prevent-top-attacks)**
>
> Discover real-world attack scenarios, security best practices, and how our gateway protects your AI applications.

## Overview

This Secure MCP Gateway is built with authentication, automatic tool discovery, caching, and guardrail enforcement.

It sits between your MCP client and MCP servers. So, by it's nature it itself also acts as an MCP server as well as an MCP client :)

When your MCP client connects to the Gateway, it acts as an MCP server. When the Gateway connects to the actual MCP server, it acts as an MCP client.

- [Pypi Package](https://pypi.org/project/secure-mcp-gateway/)

- [Docker Image](https://hub.docker.com/r/enkryptai/secure-mcp-gateway)

- Also see:
  - [CLI-Commands-Reference.md](./CLI-Commands-Reference.md) for the list of commands and their usage
  - [API-Reference.md](./API-Reference.md) for the list of API endpoints and their usage
  - [MCP Gateway Setup Notebook](./mcp_gateway_setup.ipynb) for a complete walkthrough of all the essential commands

## Table of Contents

- [1. Features 🚀](#1-features)
  <!-- - [1.1 Guardrails 🔒 🚧](#11-guardrails)

  - [1.2 Concepts 💡](#12-concepts) -->

- [2. High level steps of how the MCP Gateway works 🪜](#2-high-level-steps-of-how-the-mcp-gateway-works)

- [3. Prerequisites 🧩](#3-prerequisites)

- [4. Gateway Setup 👨‍💻](#4-gateway-setup)
  <!-- - [4.1 Local Installation with pip 📦](#41-local-installation-with-pip)

  - [4.2 Local Installation with git clone 🗂️](#42-local-installation-with-git-clone)
   - [4.2.1 Clone the repo, setup virtual environment and install dependencies 📥](#421-clone-the-repo-setup-virtual-environment-and-install-dependencies)
   - [4.2.2 Run the setup script 📥](#422-run-the-setup-script)
   - [4.2.3 Setup Other MCP Clients 🤖](#423-setup-other-mcp-clients)
  - [4.3 Docker Installation 🐳](#43-docker-installation)
  - [4.4 Remote Installation 🌐](#44-remote-installation) -->

- [5. (Optional) OpenTelemetry Setup 📊](#5-optional-opentelemetry-setup)

- [6. Verify Installation and check the files generated ✅](#6-verify-installation-and-check-the-files-generated)
  <!-- - [6.1 Verify Claude Desktop 🔍](#61-verify-claude-desktop)

  - [6.2 Example MCP config file generated 📄](#62-example-mcp-config-file-generated)
  - [6.3 Restart Claude Desktop to run the Gateway 🔄](#63-restart-claude-desktop-to-run-the-gateway)
  - [6.4 Example prompts 💬](#64-example-prompts)
  - [6.5 Example config file generated ⚙️](#65-example-config-file-generated)
  - [6.6 Verify Cursor 🔍](#66-verify-cursor) -->

- [7. Edit the Gateway config as needed ✏️](#7-edit-the-gateway-config-as-needed)

- [8. (Optional) Add GitHub MCP Server to the Gateway 🤖](#8-optional-add-github-mcp-server-to-the-gateway)

- [8.1 (Optional) Connect to MCP Servers with OAuth 🔐](#81-optional-connect-to-mcp-servers-with-oauth)

- [9. (Optional) Protect GitHub MCP Server and Test Echo Server 🔒](#9-optional-protect-github-mcp-server-and-test-echo-server)

- [10. Recommendations for using Guardrails 💡](#10-recommendations-for-using-guardrails)

- [11. Other tools available 🔧](#11-other-tools-available)

- [12. Deployment Patterns 🪂](#12-deployment-patterns)

- [13. Uninstall the Gateway 🗑️](#13-uninstall-the-gateway)

- [14. Troubleshooting 🕵](#14-troubleshooting)

- [15. Known Issues being worked on 🏗️](#15-known-issues-being-worked-on)

- [16. Known Limitations ⚠️](#16-known-limitations)

- [17. Contribute 🤝](#17-contribute)

## 1. Features

![enkrypt-secure-mcp-gateway-features](./docs/images/enkrypt-secure-mcp-gateway-features.png)

Below are the list of features Enkrypt AI Secure MCP Gateway provides:

1. **Authentication**: We use Unique Key to authenticate with the Gateway. We also use Enkrypt API Key if you want to protect your MCPs with Enkrypt Guardrails

2. **Ease of use**: You can configure all your MCP servers locally in the config file or better yet in Enkrypt *(Coming soon)* and use them in the Gateway by using their name

3. **Dynamic Tool Discovery**: The Gateway discovers tools from the MCP servers dynamically and makes them available to the MCP client

4. **Restrict Tool Invocation**: If you don't want all tools to be accessible of a an MCP server, you can restrict them by explicitly mentioning the tools in the Gateway config so that only the allowed tools are accessible to the MCP client

5. **Caching**: We cache the user gateway config and tools discovered from various MCP servers locally or in an external cache server like KeyDB if configured to improve performance

6. **Guardrails**: You can configure guardrails for each MCP server in Enkrypt both on input side (before sending the request to the MCP server) and output side (after receiving the response from the MCP server)

7. **Logging**: We log every request and response from the Gateway locally in your MCP logs and also forward them to Enkrypt *(Coming soon)* for monitoring. This enables you to see all the calls made in your account, servers used, tools invoked, requests blocked, etc.

### 1.1 Guardrails

![enkrypt-secure-mcp-gateway-guardrails](./docs/images/enkrypt-secure-mcp-gateway-guardrails.png)

**Input Protection:** Topic detection, NSFW filtering, toxicity detection, injection attack prevention, keyword detection, policy violation detection, bias detection, and PII redaction (More coming soon like system prompt protection, copyright protection, etc.)

**Output Protection:** All input protections plus adherence checking and relevancy validation (More coming soon like hallucination detection, etc.) We also auto unredact the response if it was redacted on input.

### 1.2 Concepts

- MCP Config is an array of MCP servers like `mcp_server_1`, `mcp_server_2`, `mcp_server_3` etc.
  - Each config has a unique ID

- User is a user of the gateway with unique email and ID

- A project is a collection of users that share an MCP Config
  - Project has a name and unique ID
  - The MCP Config can be updated or can be pointed to a different config by the Admin
  - Users can be added to multiple projects

- An API Key is created for a user and project combination
  - A user can have different API Keys for different projects
  - This API Key is used to authenticate the user and identify the right project and MCP Config

- *See [6.5 Example config file generated](#65-example-config-file-generated) and [7. Edit the Gateway config as needed](#7-edit-the-gateway-config-as-needed) for schema reference*

## 2. High level steps of how the MCP Gateway works

![Local Gateway with Remote Guardrails Flow](./docs/images/enkryptai-apiaas-MCP%20Gateway%20Local.drawio.png)

<br>
<details>
<summary><strong>🪜 Steps </strong></summary>
<br>

1. Your MCP client connects to the Secure MCP Gateway server with API Key (handled by `src/secure_mcp_gateway/gateway.py`).

2. Gateway server fetches gateway config from local `enkrypt_mcp_config.json` file or remote Enkrypt Auth server *(Coming soon)*.

    - It caches the config locally or in an external cache server like KeyDB if configured to improve performance.

3. If input guardrails are enabled, request is validated before the tool call (handled by `src/secure_mcp_gateway/guardrail.py`).
   - Request is blocked if it violates any of the configured guardrails and the specific detector is configured to block.

4. Requests are forwarded to the Gateway Client (handled by `src/secure_mcp_gateway/client.py`).

5. The Gateway client forwards the request to the appropriate MCP server (handled by `src/secure_mcp_gateway/client.py`).

6. The MCP server processes the request and returns the response to the Gateway client.

7. If it was a discover tools call, the Gateway client caches the tools locally or in an external cache server like KeyDB if configured. It then forwards the response to the Gateway server.

8. The Gateway server receives the response from the Gateway client and if output guardrails are enabled, it validates the response against the configured guardrails (handled by `src/secure_mcp_gateway/guardrail.py`).

    - Response is blocked if it violates any of the configured guardrails and the specific detector is configured to block.

9. The Gateway server forwards the response back to the MCP client if everything is fine.

</details>

## 3. Prerequisites

<details>
<summary><strong>🔗 Dependencies </strong></summary>

- `Git 2.43` or higher

- `Python 3.11` or higher installed on your system and is accessible from the command line using either `python` or `python3` command

- `pip 25.0.1` or higher is installed on your system and is accessible from the command line using either `pip` or `python -m pip` command

- `uv 0.7.9` or higher is installed on your system and is accessible from the command line using either `uv` or `python -m uv` command

<br>
<details>
<summary><strong>🔍 Check versions </strong></summary>

- Check if Python, pip and uv are installed

- If any of the below commands fail, please refer the respective documentation to install them properly

```bash

# ------------------

# Python

# ------------------

python --version

# Example output
Python 3.13.3

# If not, install python from their website and run the version check again

# ------------------

# pip

# ------------------
pip --version

# Example output
pip 25.0.1 from C:\Users\PC\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\pip (python 3.13)

# If not, try the following and run the version check again
python -m ensurepip

# ------------------

# uv

# ------------------

uv --version

# Or run with "python -m" if uv is not found directly

# If this works, use "python -m" before all uv commands from now on
python -m uv --version

# Example output
uv 0.7.9 (13a86a23b 2025-05-30)

# If not, try the following and run the version check again
python -m pip install uv

```

</details>
</details>

<!-- - Set `PYTHONPATH` in your system environment variables

  - For reference, see [How to Add Python to PATH on Windows, Linux, and macOS](https://phoenixnap.com/kb/add-python-to-path)

    - In Windows, if you can't find python in the folder mentioned in the article, try `%USERPROFILE%\AppData\Local\Microsoft\WindowsApps` -->

- Install **Claude Desktop** as the MCP Client from [their website](https://claude.ai/download) if you haven't already and login to it

  - *If you are using Linux and cannot run any [unofficial version](https://www.greghilston.com/post/claude-desktop-on-linux/) of Claude Desktop, you can use [any supported MCP Client](https://modelcontextprotocol.io/quickstart/server#testing-your-server-with-claude-for-desktop) to test the Gateway. If it does not support mcp cli `mcp install` command, then go through the scripts code and run the commands supported manually.*

- Any other dependencies required for the MCP servers we want to proxy requests to

  - Follow the instructions of the respective MCP server to install its dependencies

  - Like `Node.js`, `npx`, `docker`, etc.

- (Optional) A cache server like KeyDB installed and running (If you want to cache externally and not locally)

<br>
<details>
<summary><strong>🔒 Optional Protection with Enkrypt Guardrails </strong></summary>
<br>

If you want to protect your MCPs with Enkrypt Guardrails, you need to do the following:

- Create a new account if you don't have one. It's free! 🆓 No credit card required 💳🚫

- An `ENKRYPT_API_KEY` which you can get from [Enkrypt Dashboard Settings](https://app.enkryptai.com/settings)

- To protect your MCPs with Guardrails, you can use the default sample Guardrail `Sample Airline Guardrail` to get started or you can create your own custom Guardrail

- To configure custom Guardrails, you need to either login to Enkrypt AI App or use the APIs/SDK

  - [Create Guardrails in Enkrypt AI App Dashboard ✅](https://app.enkryptai.com/guardrails)

  - [Create Guardrails using APIs](https://docs.enkryptai.com/guardrails-api-reference/endpoint/add-policy)

  - [Create Guardrails using SDK](https://docs.enkryptai.com/libraries/python/introduction#guardrails-policy-management)

  - [You can also use Enkrypt MCP Server 🤯 to create Guardrails and use them in the Gateway](https://github.com/enkryptai/enkryptai-mcp-server)

</details>

## 4. Gateway Setup

### 4.1 Local Installation with pip

<details>
<summary><strong>📦 Pip Installation Steps </strong></summary>

#### 4.1.1 Download and Install the Package

- Activate a virtual environment

  ```bash
  python -m venv .secure-mcp-gateway-venv

  # Activate the virtual environment
  # On Windows
  .secure-mcp-gateway-venv\Scripts\activate

  # On Linux/macOS
  source .secure-mcp-gateway-venv/bin/activate

  # Run the below to exit the virtual environment later if needed
  deactivate
  ```

- Install the package. For more info see [https://pypi.org/project/secure-mcp-gateway/](https://pypi.org/project/secure-mcp-gateway/)

  ```bash
  pip install secure-mcp-gateway
  ```

#### 4.1.2 Run the Generate Command

- **This generates the config file at `~/.enkrypt/enkrypt_mcp_config.json` on macOS and `%USERPROFILE%\.enkrypt\enkrypt_mcp_config.json` on Windows**

  ```bash
  secure-mcp-gateway generate-config
  ```

<details>
<summary><strong>🖨️ Example output</strong></summary>
<br>

```bash
Initializing Enkrypt Secure MCP Gateway
Initializing Enkrypt Secure MCP Gateway Common Utilities Module
Initializing Enkrypt Secure MCP Gateway Module
--------------------------------
SYSTEM INFO:
Using Python interpreter: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Scripts\python.exe
Python version: 3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]
Current working directory: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway
PYTHONPATH: Not set
--------------------------------
Installing dependencies...
All dependencies installed successfully.
Initializing Enkrypt Secure MCP Gateway Client Module
Initializing Enkrypt Secure MCP Gateway Guardrail Module
Error: Gateway key is required. Please update your mcp client config and try again.
Getting Enkrypt Common Configuration
config_path: C:\Users\PC\.enkrypt\enkrypt_mcp_config.json
example_config_path: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Lib\site-packages\secure_mcp_gateway\example_enkrypt_mcp_config.json
No enkrypt_mcp_config.json file found. Defaulting to example_enkrypt_mcp_config.json
--------------------------------
ENKRYPT_GATEWAY_KEY: ****NULL
enkrypt_log_level: info
is_debug_log_level: False
enkrypt_base_url: https://api.enkryptai.com
enkrypt_use_remote_mcp_config: False
enkrypt_api_key: ****_KEY
enkrypt_tool_cache_expiration: 4
enkrypt_gateway_cache_expiration: 24
enkrypt_mcp_use_external_cache: False
enkrypt_async_input_guardrails_enabled: False
--------------------------------
External Cache is not enabled. Using local cache only.
Initializing Enkrypt Secure MCP Gateway CLI Module
Generated default config at C:\Users\PC\.enkrypt\enkrypt_mcp_config.json

```

</details>

#### 4.1.3 Example of the generated config file

<details>
<summary><strong>🍎 Example file in macOS</strong></summary>
<br>

- This is an example of the default configuration file generated by the CLI on macOS:

```json
{
  "common_mcp_gateway_config": {
    "enkrypt_log_level": "INFO",
    "enkrypt_base_url": "https://api.enkryptai.com",
    "enkrypt_api_key": "YOUR_ENKRYPT_API_KEY",
    "enkrypt_use_remote_mcp_config": false,
    "enkrypt_remote_mcp_gateway_name": "enkrypt-secure-mcp-gateway-1",
    "enkrypt_remote_mcp_gateway_version": "v1",
    "enkrypt_mcp_use_external_cache": false,
    "enkrypt_cache_host": "localhost",
    "enkrypt_cache_port": 6379,
    "enkrypt_cache_db": 0,
    "enkrypt_cache_password": null,
    "enkrypt_tool_cache_expiration": 4,
    "enkrypt_gateway_cache_expiration": 24,
    "enkrypt_async_input_guardrails_enabled": false,
    "enkrypt_async_output_guardrails_enabled": false,
    "enkrypt_telemetry": {
      "enabled": true,
      "insecure": true,
      "endpoint": "http://localhost:4317"
    }
  },
  "mcp_configs": {
    "fcbd4508-1432-4f13-abb9-c495c946f638": {
      "mcp_config_name": "default_config",
      "mcp_config": [
        {
          "server_name": "echo_server",
          "description": "Simple Echo Server",
          "config": {
            "command": "python",
            "args": [
              "/Users/user/enkryptai/secure-mcp-gateway/venv/lib/python3.13/site-packages/secure_mcp_gateway/bad_mcps/echo_mcp.py"
            ]
          },
          "tools": {},
          "input_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "pii_redaction": false
            },
            "block": [
              "policy_violation"
            ]
          },
          "output_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "relevancy": false,
              "hallucination": false,
              "adherence": false
            },
            "block": [
              "policy_violation"
            ]
          }
        }
      ]
    }
  },
  "projects": {
    "3c09f06c-1f0d-4153-9ac5-366397937641": {
      "project_name": "default_project",
      "mcp_config_id": "fcbd4508-1432-4f13-abb9-c495c946f638",
      "users": [
        "6469a670-1d64-4da5-b2b3-790de21ac726"
      ],
      "created_at": "2025-07-16T17:02:00.406877"
    }
  },
  "users": {
    "6469a670-1d64-4da5-b2b3-790de21ac726": {
      "email": "default@example.com",
      "created_at": "2025-07-16T17:02:00.406902"
    }
  },
  "apikeys": {
    "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat": {
      "project_id": "3c09f06c-1f0d-4153-9ac5-366397937641",
      "user_id": "6469a670-1d64-4da5-b2b3-790de21ac726",
      "created_at": "2025-07-16T17:02:00.406905"
    }
  }
}

```

</details>
<details>
<summary><strong>🪟 Example file in Windows</strong></summary>
<br>

- This is an example of the default configuration file generated by the CLI on Windows:

```json
{
  "common_mcp_gateway_config": {
    "enkrypt_log_level": "INFO",
    "enkrypt_base_url": "https://api.enkryptai.com",
    "enkrypt_api_key": "YOUR_ENKRYPT_API_KEY",
    "enkrypt_use_remote_mcp_config": false,
    "enkrypt_remote_mcp_gateway_name": "enkrypt-secure-mcp-gateway-1",
    "enkrypt_remote_mcp_gateway_version": "v1",
    "enkrypt_mcp_use_external_cache": false,
    "enkrypt_cache_host": "localhost",
    "enkrypt_cache_port": 6379,
    "enkrypt_cache_db": 0,
    "enkrypt_cache_password": null,
    "enkrypt_tool_cache_expiration": 4,
    "enkrypt_gateway_cache_expiration": 24,
    "enkrypt_async_input_guardrails_enabled": false,
    "enkrypt_async_output_guardrails_enabled": false,
    "enkrypt_telemetry": {
      "enabled": true,
      "insecure": true,
      "endpoint": "http://localhost:4317"
    }
  },
  "mcp_configs": {
    "fcbd4508-1432-4f13-abb9-c495c946f638": {
      "mcp_config_name": "default_config",
      "mcp_config": [
        {
          "server_name": "echo_server",
          "description": "Simple Echo Server",
          "config": {
            "command": "python",
            "args": [
              "C:\\Users\\<User>\\Documents\\GitHub\\EnkryptAI\\secure-mcp-gateway\\.secure-mcp-gateway-venv\\Lib\\site-packages\\secure_mcp_gateway\\bad_mcps\\echo_mcp.py"
            ]
          },
          "tools": {},
          "input_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "pii_redaction": false
            },
            "block": [
              "policy_violation"
            ]
          },
          "output_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "relevancy": false,
              "hallucination": false,
              "adherence": false
            },
            "block": [
              "policy_violation"
            ]
          }
        }
      ]
    }
  },
  "projects": {
    "3c09f06c-1f0d-4153-9ac5-366397937641": {
      "project_name": "default_project",
      "mcp_config_id": "fcbd4508-1432-4f13-abb9-c495c946f638",
      "users": [
        "6469a670-1d64-4da5-b2b3-790de21ac726"
      ],
      "created_at": "2025-07-16T17:02:00.406877"
    }
  },
  "users": {
    "6469a670-1d64-4da5-b2b3-790de21ac726": {
      "email": "default@example.com",
      "created_at": "2025-07-16T17:02:00.406902"
    }
  },
  "apikeys": {
    "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat": {
      "project_id": "3c09f06c-1f0d-4153-9ac5-366397937641",
      "user_id": "6469a670-1d64-4da5-b2b3-790de21ac726",
      "created_at": "2025-07-16T17:02:00.406905"
    }
  }
}

```

</details>

#### 4.1.4 Install the Gateway for Claude Desktop

- Run the following command to install the gateway for Claude:

  ```bash
  secure-mcp-gateway install --client claude-desktop
  ```

- This will register Enkrypt Secure MCP Gateway with Claude Desktop.

- **NOTE: Please restart Claude Desktop after installation**

<details>
<summary><strong>🖨️ Example output</strong></summary>
<br>

```bash
Initializing Enkrypt Secure MCP Gateway
Initializing Enkrypt Secure MCP Gateway Common Utilities Module
Initializing Enkrypt Secure MCP Gateway Module
--------------------------------
SYSTEM INFO:
Using Python interpreter: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Scripts\python.exe
Python version: 3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]
Current working directory: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway
PYTHONPATH: Not set
--------------------------------
Installing dependencies...
All dependencies installed successfully.
Initializing Enkrypt Secure MCP Gateway Client Module
Initializing Enkrypt Secure MCP Gateway Guardrail Module
Error: Gateway key is required. Please update your mcp client config and try again.
Getting Enkrypt Common Configuration
config_path: C:\Users\PC\.enkrypt\enkrypt_mcp_config.json
example_config_path: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Lib\site-packages\secure_mcp_gateway\example_enkrypt_mcp_config.json
Loading enkrypt_mcp_config.json file...
--------------------------------
ENKRYPT_GATEWAY_KEY: ****NULL
enkrypt_log_level: info
is_debug_log_level: False
enkrypt_base_url: https://api.enkryptai.com
enkrypt_use_remote_mcp_config: False
enkrypt_api_key: ****_KEY
enkrypt_tool_cache_expiration: 4
enkrypt_gateway_cache_expiration: 24
enkrypt_mcp_use_external_cache: False
enkrypt_async_input_guardrails_enabled: False
--------------------------------
External Cache is not enabled. Using local cache only.
Initializing Enkrypt Secure MCP Gateway CLI Module
CONFIG_PATH:  C:\Users\PC\.enkrypt\enkrypt_mcp_config.json
GATEWAY_PY_PATH:  C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Lib\site-packages\secure_mcp_gateway\gateway.py
client name from args:  claude-desktop
Successfully installed gateway for claude-desktop
Path to gateway is incorrect. Modifying the path to gateway in claude_desktop_config.json file...
Path to gateway modified in claude_desktop_config.json file
Please restart Claude Desktop to use the gateway.

```

</details>

#### 4.1.5 Example of the Claude Desktop Config after installation

<details>
<summary><strong>🍎 Example file in macOS</strong></summary>
<br>

- `~/Library/Application Support/Claude/claude_desktop_config.json`

  ```json
  {
    "mcpServers": {
      "Enkrypt Secure MCP Gateway": {
        "command": "/opt/homebrew/bin/uv",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "mcp",
          "run",
          "/Users/user/enkryptai/secure-mcp-gateway/venv/lib/python3.13/site-packages/secure_mcp_gateway/gateway.py"
        ],
        "env": {
          "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
          "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
          "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
        }
      }
    }
  }
  ```

</details>
<details>
<summary><strong>🪟 Example file in Windows</strong></summary>
<br>

- `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`

  ```json
  {
    "mcpServers": {
      "Enkrypt Secure MCP Gateway": {
        "command": "C:\\Users\\<User>\\.local\\bin\\uv.EXE",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "mcp",
          "run",
          "C:\\Users\\<User>\\Documents\\GitHub\\EnkryptAI\\secure-mcp-gateway\\.secure-mcp-gateway-venv\\Lib\\site-packages\\secure_mcp_gateway\\gateway.py"
        ],
        "env": {
          "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
          "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
          "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
        }
      }
    }
  }
  ```

</details>

#### 4.1.6 Install the Gateway for Cursor

- Run the CLI Install Command for Cursor

  ```bash
  secure-mcp-gateway install --client cursor
  ```

- This automatically updates your ~/.cursor/mcp.json (on Windows it is at: %USERPROFILE%\.cursor\mcp.json) with the correct entry.

- *Although it is not usually required to restart, if you see it in loading state for a long time, please restart Cursor*

<details>
<summary><strong>🍎 Example file in macOS</strong></summary>
<br>

- `~/.cursor/mcp.json`

  ```json
  {
    "mcpServers": {
      "Enkrypt Secure MCP Gateway": {
        "command": "uv",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "mcp",
          "run",
          "/Users/user/enkryptai/secure-mcp-gateway/venv/lib/python3.13/site-packages/secure_mcp_gateway/gateway.py"
        ],
        "env": {
          "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
          "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
          "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
        }
      }
    }
  }
  ```

</details>
<details>
<summary><strong>🪟 Example file in Windows</strong></summary>
<br>

- `%USERPROFILE%\.cursor\mcp.json`

  ```json
  {
    "mcpServers": {
      "Enkrypt Secure MCP Gateway": {
        "command": "uv",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "mcp",
          "run",
          "C:\\Users\\<User>\\Documents\\GitHub\\EnkryptAI\\secure-mcp-gateway\\.secure-mcp-gateway-venv\\Lib\\site-packages\\secure_mcp_gateway\\gateway.py"
        ],
        "env": {
          "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
          "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
          "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
        }
      }
    }
  }
  ```

</details>

</details>

### 4.2 Local Installation with git clone

<details>
<summary><strong>🗂️ Git Clone Installation Steps </strong></summary>

#### 4.2.1 Clone the repo, setup virtual environment and install dependencies

- Clone the repository:

```bash
git clone https://github.com/enkryptai/secure-mcp-gateway

cd secure-mcp-gateway

```

<br>
<details>
<summary><strong>⚡ Activate a virtual environment </strong></summary>
<br>

```bash

# ------------------

# Create a virtual environment

# ------------------

uv venv

# Example output
Using CPython 3.13.3 interpreter at: C:\Users\PC\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate

# ------------------

# Activate the virtual environment

# ------------------

# For 🍎 Linux/macOS, run the following
source ./.venv/Scripts/activate

# For 🪟 Windows, run the following
.\.venv\Scripts\activate

# After activating, you should see (enkrypt-secure-mcp-gateway) before the file path in the terminal

# Example:

# (enkrypt-secure-mcp-gateway) %USERPROFILE%\Documents\GitHub\EnkryptAI\secure-mcp-gateway>

# ------------------

# Install pip in the virtual environment

# ------------------

python -m ensurepip

# ------------------

# Install uv in the virtual environment

# ------------------

python -m pip install uv

```

- Install Python dependencies:

```bash
uv pip install -r requirements.txt

```

- Verify mcp cli got installed successfully:

```bash
mcp version

# Example output
MCP version 1.9.2

```

</details>

#### 4.2.2 Run the setup script

<!-- - The `setup` script checks versions of Python, pip, uv and makes sure they are installed and accessible -->

<!-- - It then installs the dependencies -->

- This script creates the config file at `~/.enkrypt/enkrypt_mcp_config.json` on macOS and `%USERPROFILE%\.enkrypt\enkrypt_mcp_config.json` on Windows based on `src/secure_mcp_gateway/example_enkrypt_mcp_config.json` file

- It replaces `UNIQUE_GATEWAY_KEY` and other `UUIDs` with auto generated values and also replaces `DUMMY_MCP_FILE_PATH` with the actual path to the test MCP file `bad_mcps/echo_mcp.py`

- It also installs the MCP client in Claude Desktop

- *NOTE: Please restart Claude Desktop after running the setup script to see the Gateway running in Claude Desktop*

```bash

# On 🍎 Linux/macOS run the below
cd scripts
chmod +x *.sh
./setup.sh

# On 🪟 Windows run the below
cd scripts
setup.bat

# Now restart Claude Desktop to see the Gateway running

```

<br>
<details>
<summary><strong>🖨️ Example output</strong></summary>
<br>

```bash
-------------------------------
Setting up Enkrypt Secure MCP Gateway enkrypt_mcp_config.json config file
-------------------------------
        1 file(s) copied.
Generated unique gateway key: WTZOpoU1mXJz8b_ZJQ42DuSXlQCSCtWOn3FX0jG8sO_FKYNJetjYEgSluvhtBN8_
Generated unique uuid: 7920749a-228e-47fe-a6a9-cd2d64a2283b
DUMMY_MCP_FILE_PATH: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\src\secure_mcp_gateway\bad_mcps\echo_mcp.py
-------------------------------
Setup complete. Please check the enkrypt_mcp_config.json file in the ~\.enkrypt directory and update with your MCP server configs as needed.
-------------------------------
-------------------------------
Installing Enkrypt Secure MCP Gateway with gateway key and dependencies
-------------------------------
mcp is installed. Proceeding with installation...
ENKRYPT_GATEWAY_KEY: WTZOpoU1mXJz8b_ZJQ42DuSXlQCSCtWOn3FX0jG8sO_FKYNJetjYEgSluvhtBN8_
The system cannot find the path specified.
Package names only:
Dependencies string for the cli install command:
Running the cli install command: mcp install gateway.py --env-var ENKRYPT_GATEWAY_KEY=WTZOpoU1mXJz8b_ZJQ42DuSXlQCSCtWOn3FX0jG8sO_FKYNJetjYEgSluvhtBN8_
Initializing Enkrypt Secure MCP Gateway
Initializing Enkrypt Secure MCP Gateway Common Utilities Module
Initializing Enkrypt Secure MCP Gateway Module
--------------------------------
SYSTEM INFO:
Using Python interpreter: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Scripts\python.exe
Python version: 3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]
Current working directory: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\src\secure_mcp_gateway
PYTHONPATH: Not set
--------------------------------
Installing dependencies...
All dependencies installed successfully.
Initializing Enkrypt Secure MCP Gateway Client Module
Initializing Enkrypt Secure MCP Gateway Guardrail Module
Getting Enkrypt Common Configuration
config_path: C:\Users\PC\.enkrypt\enkrypt_mcp_config.json
example_config_path: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Lib\site-packages\secure_mcp_gateway\example_enkrypt_mcp_config.json
Loading enkrypt_mcp_config.json file...
--------------------------------
ENKRYPT_GATEWAY_KEY: ****BN8_
enkrypt_log_level: info
is_debug_log_level: False
enkrypt_base_url: https://api.enkryptai.com
enkrypt_use_remote_mcp_config: False
enkrypt_api_key: ****_KEY
enkrypt_tool_cache_expiration: 4
enkrypt_gateway_cache_expiration: 24
enkrypt_mcp_use_external_cache: False
enkrypt_async_input_guardrails_enabled: False
--------------------------------
External Cache is not enabled. Using local cache only.
Initializing Enkrypt Secure MCP Gateway Module
--------------------------------
SYSTEM INFO:
Using Python interpreter: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Scripts\python.exe
Python version: 3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]
Current working directory: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\src\secure_mcp_gateway
PYTHONPATH: Not set
--------------------------------
Installing dependencies...
All dependencies installed successfully.
Getting Enkrypt Common Configuration
config_path: C:\Users\PC\.enkrypt\enkrypt_mcp_config.json
example_config_path: C:\Users\PC\Documents\GitHub\EnkryptAI\secure-mcp-gateway\.secure-mcp-gateway-venv\Lib\site-packages\secure_mcp_gateway\example_enkrypt_mcp_config.json
Loading enkrypt_mcp_config.json file...
--------------------------------
ENKRYPT_GATEWAY_KEY: ****BN8_
enkrypt_log_level: info
is_debug_log_level: False
enkrypt_base_url: https://api.enkryptai.com
enkrypt_use_remote_mcp_config: False
enkrypt_api_key: ****_KEY
enkrypt_tool_cache_expiration: 4
enkrypt_gateway_cache_expiration: 24
enkrypt_mcp_use_external_cache: False
enkrypt_async_input_guardrails_enabled: False
--------------------------------
External Cache is not enabled. Using local cache only.
[06/15/25 13:14:10] INFO     Added server 'Enkrypt Secure MCP Gateway' to Claude config                                                                                                             claude.py:137
                    INFO     Successfully installed Enkrypt Secure MCP Gateway in Claude app                                                                                                           cli.py:486
-------------------------------
Installation complete. Check the claude_desktop_config.json file as per the readme instructions and restart Claude Desktop.
-------------------------------

```

</details>

#### 4.2.3 Setup Other MCP Clients

<details>
<summary><strong>⬡ Cursor </strong></summary>
<br>

- You can navigate to cursor's **Global MCP** file at `~/.cursor/mcp.json` on Linux/macOS or `%USERPROFILE%\.cursor\mcp.json` on Windows

  - If you would like to use at a **Project level** place it inside your project. For details see [Cursor's docs](https://docs.cursor.com/context/model-context-protocol#configuration-locations)

- You can also navigate to the file Via cursor's UI by clicking on `settings` gear icon on the top right

  ![cursor-settings-icon](./docs/images/cursor-settings-icon.png)

- Click on `MCP` and then click on `Add new global MCP server` which takes you to the `mcp.json` file

  ![cursor-settings-mcp](./docs/images/cursor-settings-mcp.png)

- Example `mcp.json` file opened in the editor

  ![cursor-mcp-file](./docs/images/cursor-mcp-file.png)

- Once the file is opened at Global or Project level, you can copy paste the same config we used in `Claude Desktop`. For reference, you can refer to [Installation - 5.2 Example MCP config file generated 📄](#52-example-mcp-config-file-generated)

  - *Be sure to use your own file that was generated by the `setup` script in [Installation - 4.2.2 Run the setup script 📥](#422-run-the-setup-script). Please do not copy paste the example config file in this repo.*

- See [Verify Cursor](#56-verify-cursor) section to verify the MCP server is running in Cursor

</details>
</details>

### 4.3 Docker Installation

<details>
<summary><strong>🐳 Docker Installation Steps </strong></summary>

#### 4.3.1 Build the Docker Image

```bash
docker build -t secure-mcp-gateway .

```

<details>
<summary><strong>🖨️ Example output</strong></summary>
<br>

```bash
[+] Building 72.9s (20/20) FINISHED                                                                                                                                          docker:default
 => [internal] load build definition from Dockerfile                                                                                                                                   0.1s
 => => transferring dockerfile: 724B                                                                                                                                                   0.1s
 => [internal] load metadata for docker.io/library/python:3.11-alpine                                                                                                                  1.0s
 => [internal] load .dockerignore                                                                                                                                                      0.1s
 => => transferring context: 456B                                                                                                                                                      0.1s
 => [ 1/15] FROM docker.io/library/python:3.11-alpine@sha256:8068890a42d68ece5b62455ef327253249b5f094dcdee57f492635a40217f6a3                                                          0.0s
 => => resolve docker.io/library/python:3.11-alpine@sha256:8068890a42d68ece5b62455ef327253249b5f094dcdee57f492635a40217f6a3                                                            0.0s
 => [internal] load build context                                                                                                                                                      1.5s
 => => transferring context: 82.25kB                                                                                                                                                   1.4s
 => CACHED [ 2/15] WORKDIR /app                                                                                                                                                        0.0s
 => CACHED [ 3/15] COPY requirements.txt .                                                                                                                                             0.0s
 => [ 4/15] COPY requirements-dev.txt .                                                                                                                                                0.0s
 => [ 5/15] RUN pip install --upgrade pip && pip install -r requirements.txt && pip install -r requirements-dev.txt                                                                   38.7s
 => [ 6/15] COPY src src                                                                                                                                                               0.2s
 => [ 7/15] COPY setup.py setup.py                                                                                                                                                     0.1s
 => [ 8/15] COPY MANIFEST.in MANIFEST.in                                                                                                                                               0.1s
 => [ 9/15] COPY pyproject.toml pyproject.toml                                                                                                                                         0.1s
 => [10/15] COPY CHANGELOG.md CHANGELOG.md                                                                                                                                             0.1s
 => [11/15] COPY LICENSE.txt LICENSE.txt                                                                                                                                               0.1s
 => [12/15] COPY README.md README.md                                                                                                                                                   0.1s
 => [13/15] COPY README_PYPI.md README_PYPI.md                                                                                                                                         0.1s
 => [14/15] RUN python -m build                                                                                                                                                        8.5s
 => [15/15] RUN pip install .                                                                                                                                                          5.5s
 => exporting to image                                                                                                                                                                16.6s
 => => exporting layers                                                                                                                                                               11.8s
 => => exporting manifest sha256:47bd860c903fdefeda59364f577c487f96e1482b0e8eadef8292df86922641dc                                                                                      0.0s
 => => exporting config sha256:9d211386091dfc08fcfe80f1efb399d4a1ab80484f850476c328614ecaaefbae                                                                                        0.1s
 => => exporting attestation manifest sha256:bc85b5aaf4035e6f449d9b94567135a28a61c594fa2a507ca7fea889efbf2952                                                                          0.0s
 => => exporting manifest list sha256:7cd30cbf456ba3105d4bef7c28ea8402ec5476e4da3cd8c16b752f3214f8b3b1                                                                                 0.0s
 => => naming to docker.io/library/secure-mcp-gateway:latest                                                                                                                           0.0s
 => => unpacking to docker.io/library/secure-mcp-gateway:latest

```

</details>

#### 4.3.2 Generate the config file

- This creates a config file in the `~/.enkrypt/docker/enkrypt_mcp_config.json` file on macOS/Linux and `%USERPROFILE%\.enkrypt\docker\enkrypt_mcp_config.json` file on Windows.

```bash

# On 🍎 Linux/macOS run the below
docker run --rm -e HOST_OS=macos -e HOST_ENKRYPT_HOME=~/.enkrypt -v ~/.enkrypt:/app/.enkrypt --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli generate-config

# On 🪟 Windows run the below
docker run --rm -e HOST_OS=windows -e HOST_ENKRYPT_HOME=%USERPROFILE%\.enkrypt -v %USERPROFILE%\.enkrypt:/app/.enkrypt --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli generate-config

# If you are using 📟 Powershell, you can use the below command
docker run --rm -e HOST_OS=windows -e HOST_ENKRYPT_HOME=$env:USERPROFILE\.enkrypt -v ${env:USERPROFILE}\.enkrypt:/app/.enkrypt --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli generate-config

```

<details>
<summary><strong>🐳 Example Docker config file</strong></summary>
<br>

```json
{
  "common_mcp_gateway_config": {
    "enkrypt_log_level": "INFO",
    "enkrypt_base_url": "https://api.enkryptai.com",
    "enkrypt_api_key": "YOUR_ENKRYPT_API_KEY",
    "enkrypt_use_remote_mcp_config": false,
    "enkrypt_remote_mcp_gateway_name": "enkrypt-secure-mcp-gateway-1",
    "enkrypt_remote_mcp_gateway_version": "v1",
    "enkrypt_mcp_use_external_cache": false,
    "enkrypt_cache_host": "localhost",
    "enkrypt_cache_port": 6379,
    "enkrypt_cache_db": 0,
    "enkrypt_cache_password": null,
    "enkrypt_tool_cache_expiration": 4,
    "enkrypt_gateway_cache_expiration": 24,
    "enkrypt_async_input_guardrails_enabled": false,
    "enkrypt_async_output_guardrails_enabled": false,
    "enkrypt_telemetry": {
      "enabled": true,
      "insecure": true,
      "endpoint": "http://localhost:4317"
    }
  },
  "mcp_configs": {
    "fcbd4508-1432-4f13-abb9-c495c946f638": {
      "mcp_config_name": "default_config",
      "mcp_config": [
        {
          "server_name": "echo_server",
          "description": "Simple Echo Server",
          "config": {
            "command": "python",
            "args": [
              "/usr/local/lib/python3.11/site-packages/secure_mcp_gateway/bad_mcps/echo_mcp.py"
            ]
          },
          "tools": {},
          "input_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "pii_redaction": false
            },
            "block": [
              "policy_violation"
            ]
          },
          "output_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "relevancy": false,
              "hallucination": false,
              "adherence": false
            },
            "block": [
              "policy_violation"
            ]
          }
        }
      ]
    }
  },
  "projects": {
    "3c09f06c-1f0d-4153-9ac5-366397937641": {
      "project_name": "default_project",
      "mcp_config_id": "fcbd4508-1432-4f13-abb9-c495c946f638",
      "users": [
        "6469a670-1d64-4da5-b2b3-790de21ac726"
      ],
      "created_at": "2025-07-16T17:02:00.406877"
    }
  },
  "users": {
    "6469a670-1d64-4da5-b2b3-790de21ac726": {
      "email": "default@example.com",
      "created_at": "2025-07-16T17:02:00.406902"
    }
  },
  "apikeys": {
    "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat": {
      "project_id": "3c09f06c-1f0d-4153-9ac5-366397937641",
      "user_id": "6469a670-1d64-4da5-b2b3-790de21ac726",
      "created_at": "2025-07-16T17:02:00.406905"
    }
  }
}

```

</details>

#### 4.3.3 Install the Gateway in Claude Desktop

- You can find the Claude config location at the below locations in your system. [For reference see Claude docs.](https://modelcontextprotocol.io/quickstart/user#:~:text=This%20will%20create%20a%20configuration%20file%20at%3A)
  - macOS: `~/Library/Application Support/Claude`
  - Windows: `%APPDATA%\Claude`

```bash

# On 🍎 Linux/macOS run the below
docker run --rm -i -e HOST_OS=macos -e HOST_ENKRYPT_HOME=~/.enkrypt -v ~/.enkrypt:/app/.enkrypt -v ~/Library/Application\ Support/Claude:/app/.claude --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli install --client claude-desktop

# On 🪟 Windows run the below
docker run --rm -i -e HOST_OS=windows -e HOST_ENKRYPT_HOME=%USERPROFILE%\.enkrypt -v %USERPROFILE%\.enkrypt:/app/.enkrypt -v %APPDATA%\Claude:/app/.claude --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli install --client claude-desktop

# If you are using 📟 Powershell, you can use the below command
docker run --rm -i -e HOST_OS=windows -e HOST_ENKRYPT_HOME=$env:USERPROFILE\.enkrypt -v ${env:USERPROFILE}\.enkrypt:/app/.enkrypt -v ${env:APPDATA}\Claude:/app/.claude --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli install --client claude-desktop

```

#### 4.3.4 Example Claude Desktop config file

<details>
<summary><strong>🪟 Example Windows claude_desktop_config.json</strong></summary>
<br>

```json
{
  "mcpServers": {
    "Enkrypt Secure MCP Gateway": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "C:\\Users\\<user>\\.enkrypt:/app/.enkrypt",
        "secure-mcp-gateway"
      ],
      "env": {
        "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
        "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
        "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
      }
    }
  }
}

```

</details>

#### 4.3.5 Install the Gateway in Cursor

- You can find the Cursor config location at the below locations. [For reference see Cursor docs.](https://docs.cursor.com/context/model-context-protocol#configuration-locations)
  - macOS: `~/.cursor`
  - Windows: `%USERPROFILE%\.cursor`

```bash

# On 🍎 Linux/macOS run the below
docker run --rm -i -e HOST_OS=macos -e HOST_ENKRYPT_HOME=~/.enkrypt -v ~/.enkrypt:/app/.enkrypt -v ~/Library/Application\ Support/Cursor:/app/.cursor --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli install --client cursor

# On 🪟 Windows run the below
docker run --rm -i -e HOST_OS=windows -e HOST_ENKRYPT_HOME=%USERPROFILE%\.enkrypt -v %USERPROFILE%\.enkrypt:/app/.enkrypt -v %USERPROFILE%\.cursor:/app/.cursor --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli install --client cursor

# If you are using 📟 Powershell, you can use the below command
docker run --rm -i -e HOST_OS=windows -e HOST_ENKRYPT_HOME=$env:USERPROFILE\.enkrypt -v ${env:USERPROFILE}\.enkrypt:/app/.enkrypt -v ${env:USERPROFILE}\.cursor:/app/.cursor --entrypoint python secure-mcp-gateway -m secure_mcp_gateway.cli install --client cursor

```

</details>

### 4.4 Remote Installation

<details>
<summary><strong>🌐 Remote Installation Steps </strong></summary>

#### 4.4.1 Run the Gateway in a remote server

```bash
python gateway.py

```

- Or run in k8s using our docker image `enkryptai/secure-mcp-gateway:vx.x.x`

- Example: `enkryptai/secure-mcp-gateway:v2.1.1`

- Use the latest version from Docker Hub: <https://hub.docker.com/r/enkryptai/secure-mcp-gateway/tags>

- You can either mount the config file locally or download the json file from a remote place like `S3` using an `initContainer` and mount the volume

- See `docs/secure-mcp-gateway-manifest-example.yaml` for the complete manifest file reference

#### 4.4.2 Modify your MCP Client config to use the Gateway

- You can find the Claude config location at the below locations in your system. [For reference see Claude docs.](https://modelcontextprotocol.io/quickstart/user#:~:text=This%20will%20create%20a%20configuration%20file%20at%3A)
  - macOS: `~/Library/Application Support/Claude`
  - Windows: `%APPDATA%\Claude`

- You can find the Cursor config location at the below locations. [For reference see Cursor docs.](https://docs.cursor.com/context/model-context-protocol#configuration-locations)
  - macOS: `~/.cursor`
  - Windows: `%USERPROFILE%\.cursor`

- Replace the `ENKRYPT_GATEWAY_KEY` with the key you got from the `enkrypt_mcp_config.json` file

- Replace the `http://0.0.0.0:8000/mcp/` with the `http(s)://<remote_server_ip>:<port>/mcp/`

- If you are running this locally, you can use `http://0.0.0.0:8000/mcp/`

- You can setup ingress to route the traffic to the MCP Gateway over `https`

- Example: `https://mcp.enkryptai.com/mcp/`

- **NOTE: Please make sure node and npm are installed on the client machine**
  - To verify, run `node -v` and `npm -v`

- **NOTE: Make sure to use the trailing slash `/` in the MCP URL like `/mcp/`**

```json
{
  "mcpServers": {
    "Enkrypt Secure MCP Gateway": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://0.0.0.0:8000/mcp/",
        "--allow-http",
        "--header",
        "apikey:${ENKRYPT_GATEWAY_KEY}",
        "--header",
        "project_id:${ENKRYPT_PROJECT_ID}",
        "--header",
        "user_id:${ENKRYPT_USER_ID}"
      ],
      "env": {
        "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
        "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
        "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
      }
    }
  }
}

```

</details>

## 5. (Optional) OpenTelemetry Setup

<details>
<summary><strong>📊 OpenTelemetry Setup and Usage </strong></summary>
<br>

This section explains how to set up and use OpenTelemetry (OTEL) with the Enkrypt Secure MCP Gateway for observability.

### 5.1 Architecture

The observability stack includes:

- OpenTelemetry Collector: Collects telemetry data (traces, metrics, logs)

- Jaeger: Distributed tracing visualization

- Loki: Log aggregation and querying

- Prometheus: Metrics aggregation

- Grafana: Unified visualization for metrics and logs
  - Traces are not visible in Grafana for some reason. Please use Jaeger for traces.

### 5.2 Prerequisites

- Docker and Docker Compose installed

- Gateway installed and running (follow [section 4](#4-gateway-setup))

### 5.3 Setup Steps

1. **Start the Observability Stack**

   ```bash
   cd infra

   docker-compose up -d
   ```

2. **To stop the Observability Stack**

   ```bash
   # When we want to stop the Observability Stack, run the below command
   docker-compose down
   ```

### 5.4 Configuration

- Edit the `enkrypt_mcp_config.json` file to enable telemetry

  ```json
  {
    "common_mcp_gateway_config": {
      ...
      "enkrypt_telemetry": {
        "enabled": true,
        "insecure": true,
        "endpoint": "http://localhost:4317"
      }
    },
    ...
  }
  ```

### 5.5 Verification Steps

1. **Verify Services are Running**

   ```bash
   # On Windows
   docker ps | findstr "loki grafana jaeger otel prometheus"

   # On Linux/macOS
   docker ps | grep -E "loki|grafana|jaeger|otel|prometheus"
   ```

2. **Access Service UIs**

   - Grafana: <http://localhost:3000> (default credentials: admin/admin)

   - Jaeger: <http://localhost:16686>

   - Prometheus: <http://localhost:9090>

   - Loki: Access through Grafana

      1. Open Grafana (<http://localhost:3000>)
      2. Go to Explore (left sidebar)
      3. Select "Loki" from the data source dropdown

3. **Verify Gateway Telemetry**
   - Make test requests through the Gateway like `List all servers and tools` and `echo test`

   - Check traces in Jaeger:
      - Add optional tags like `enkrypt_email=default@example.com` or `enkrypt_project_name=default_project` or `enkrypt_mcp_config_id=fcbd4508-1432-4f13-abb9-c495c946f638` to see the traces for a specific user, project or MCP config etc.
      - We can also combine tags by separating them with spaces like `enkrypt_email=default@example.com enkrypt_project_name=default_project`
      - Look for `enkrypt_discover_all_tools` spans
      - Examine child spans for cache, tool discovery, etc.

        ![jaeger-1](./docs/images/jaeger-1.png)

   - Check metrics in Grafana:
     - Navigate to `Drilldown` -> `metrics`
     - We can filter on various labels like `email`, `user_id`, `mcp_config_id`, `project_id`, `project_name` etc.

        ![grafana-metrics-1](./docs/images/grafana-metrics-1.png)

   - Check logs in Grafana
     - Navigate to `Drilldown` -> `Logs`
     - Select label as `service_name=secure-mcp-gateway` and click `Show logs`
     - Now we can filter by various labels like `attributes_project_name`, `attributes_project_id`, `attributes_email`, `attributes_user_id`, `attributes_mcp_config_id`, `attributes_tool_name` etc.

        ![grafana-logs-1](./docs/images/grafana-logs-1.png)

   - Check Dashboards in Grafana by navigating to `Dashboards` -> `OpenTelemetry Gateway Metrics`
      - **Due to issues in Grafana, you may need to edit each tile and click `Run queries` to see the data**

### 5.6 Available Telemetry (Not exhaustive)

1. **Traces**
   - Request processing pipeline
   - Tool invocations with duration tracking
   - Cache operations (hits/misses)
   - Guardrail checks
   - Error tracking and status monitoring
   - Detailed attributes for debugging

2. **Metrics**
   - `enkrypt_list_all_servers_calls`: API endpoint usage
   - `mcp_cache_misses_total`: Cache efficiency tracking
   - `enkrypt_servers_discovered`: Server discovery monitoring
   - `mcp_tool_calls_total`: Tool invocation tracking
   - `mcp_tool_call_duration_seconds`: Performance monitoring (histogram)

3. **Logs**
   - Structured JSON format for better querying
   - Gateway operations with context
   - Error conditions with stack traces
   - Security events and guardrail checks
   - Performance data with timing information

</details>

## 6. Verify Installation and check the files generated

<details>
<summary><strong>✅ Verification steps and files generated</strong></summary>

### 6.1 Verify Claude Desktop

- To verify Claude installation, navigate to `claude_desktop_config.json` file by [following these instructions](https://modelcontextprotocol.io/quickstart/user#2-add-the-filesystem-mcp-server)

  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### 6.2 Example MCP config file generated

<details>
<summary><strong>🍎 Example file in macOS</strong></summary>
<br>

- `~/Library/Application Support/Claude/claude_desktop_config.json`

  ```json
  {
    "mcpServers": {
      "Enkrypt Secure MCP Gateway": {
        "command": "/opt/homebrew/bin/uv",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "mcp",
          "run",
          "/Users/user/enkryptai/secure-mcp-gateway/src/secure_mcp_gateway/gateway.py"
        ],
        "env": {
          "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
          "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
          "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
        }
      }
    }
  }
  ```

</details>
<details>
<summary><strong>🪟 Example file in Windows</strong></summary>
<br>

- `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`

  ```json
  {
    "mcpServers": {
      "Enkrypt Secure MCP Gateway": {
        "command": "C:\\Users\\<User>\\.local\\bin\\uv.EXE",
        "args": [
          "run",
          "--with",
          "mcp[cli]",
          "mcp",
          "run",
          "C:\\Users\\<User>\\Documents\\GitHub\\EnkryptAI\\secure-mcp-gateway\\src\\secure_mcp_gateway\\gateway.py"
        ],
        "env": {
          "ENKRYPT_GATEWAY_KEY": "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat",
          "ENKRYPT_PROJECT_ID": "3c09f06c-1f0d-4153-9ac5-366397937641",
          "ENKRYPT_USER_ID": "6469a670-1d64-4da5-b2b3-790de21ac726"
        }
      }
    }
  }
  ```

</details>

### 6.3 Restart Claude Desktop to run the Gateway

- After restarting, navigate to Claude Desktop `Settings`

  ![Claude Desktop Settings](./docs/images/claude-desktop-settings.png)

- Click on `Developer` -> `Enkrypt Secure MCP Gateway`

  ![Claude Desktop MCP Gateway Running](./docs/images/claude-desktop-mcp-running.png)

<br>
<details>
<summary><strong>🧰 Check tools and logs </strong></summary>
<br>

- You can also click on the settings icon below the search bar to see the Gateway in available

  ![Claude Desktop Gateway in Search](./docs/images/claude-desktop-gateway-in-search.png)

- Click on `Enkrypt Secure MCP Gateway` to see the list of tools available

  ![Claude Desktop MCP Gateway Tools](./docs/images/claude-desktop-gateway-tools-in-search.png)

- You can check Claude logs while asking Claude to do something to see the Gateway in action

  - Example 🍎 Linux/macOS log path: `~/Library/Application Support/Claude/logs/mcp-server-Enkrypt Secure MCP Gateway.log`

  - Example 🪟 Windows log path: `%USERPROFILE%\AppData\Roaming\Claude\logs\mcp-server-Enkrypt Secure MCP Gateway.log`

</details>

### 6.4 Example prompts

- `list all servers, get all tools available and echo test`
  - This uses a test MCP server `echo_server` which is in `bad_mcps/echo_mcp.py`

![claude-mcp-chat-1](./docs/images/claude-mcp-chat-1.png)

<br>
<details>
<summary><strong>💡 Other examples</strong></summary>
<br>

- We can also combine multiple prompts into one that trigger multiple tool calls at once

- Example: `echo test and also echo best`

![claude-mcp-chat-multiple](./docs/images/claude-mcp-chat-multiple.png)

- **Example: `echo "hello; ls -la; whoami"`**

- This could be a malicious prompt but because no guardrails are enabled, it will not be blocked

![claude-mcp-chat-echo-not-blocked](./docs/images/claude-mcp-chat-echo-not-blocked.png)

</details>

### 6.5 Example config file generated

- Example `enkrypt_mcp_config.json` generated by the `setup` script in `~/.enkrypt/enkrypt_mcp_config.json` on macOS and `%USERPROFILE%\.enkrypt\enkrypt_mcp_config.json` on Windows

- *If you ran docker command to install the Gateway, the config file will be in `~/.enkrypt/docker/enkrypt_mcp_config.json` on macOS and `%USERPROFILE%\.enkrypt\docker\enkrypt_mcp_config.json` on Windows*

  ```json
  {
    "common_mcp_gateway_config": {
      "enkrypt_log_level": "INFO",
      "enkrypt_base_url": "https://api.enkryptai.com",
      "enkrypt_api_key": "YOUR_ENKRYPT_API_KEY",
      "enkrypt_use_remote_mcp_config": false,
      "enkrypt_remote_mcp_gateway_name": "enkrypt-secure-mcp-gateway-1",
      "enkrypt_remote_mcp_gateway_version": "v1",
      "enkrypt_mcp_use_external_cache": false,
      "enkrypt_cache_host": "localhost",
      "enkrypt_cache_port": 6379,
      "enkrypt_cache_db": 0,
      "enkrypt_cache_password": null,
      "enkrypt_tool_cache_expiration": 4,
      "enkrypt_gateway_cache_expiration": 24,
      "enkrypt_async_input_guardrails_enabled": false,
      "enkrypt_async_output_guardrails_enabled": false,
      "enkrypt_telemetry": {
        "enabled": true,
        "insecure": true,
        "endpoint": "http://localhost:4317"
      }
    },
    "mcp_configs": {
      "fcbd4508-1432-4f13-abb9-c495c946f638": {
        "mcp_config_name": "default_config",
        "mcp_config": [
          {
            "server_name": "echo_server",
            "description": "Simple Echo Server",
            "config": {
              "command": "python",
              "args": [
                "C:\\Users\\<User>\\Documents\\GitHub\\EnkryptAI\\secure-mcp-gateway\\src\\secure_mcp_gateway\\bad_mcps\\echo_mcp.py"
              ]
            },
            "tools": {},
            "input_guardrails_policy": {
              "enabled": false,
              "policy_name": "Sample Airline Guardrail",
              "additional_config": {
                "pii_redaction": false
              },
              "block": [
                "policy_violation"
              ]
            },
            "output_guardrails_policy": {
              "enabled": false,
              "policy_name": "Sample Airline Guardrail",
              "additional_config": {
                "relevancy": false,
                "hallucination": false,
                "adherence": false
              },
              "block": [
                "policy_violation"
              ]
            }
          }
        ]
      }
    },
    "projects": {
      "3c09f06c-1f0d-4153-9ac5-366397937641": {
        "project_name": "default_project",
        "mcp_config_id": "fcbd4508-1432-4f13-abb9-c495c946f638",
        "users": [
          "6469a670-1d64-4da5-b2b3-790de21ac726"
        ],
        "created_at": "2025-07-16T17:02:00.406877"
      }
    },
    "users": {
      "6469a670-1d64-4da5-b2b3-790de21ac726": {
        "email": "default@example.com",
        "created_at": "2025-07-16T17:02:00.406902"
      }
    },
    "apikeys": {
      "2W8UupCkazk4SsOcSu_1hAbiOgPdv0g-nN9NtfZyg-rvYGat": {
        "project_id": "3c09f06c-1f0d-4153-9ac5-366397937641",
        "user_id": "6469a670-1d64-4da5-b2b3-790de21ac726",
        "created_at": "2025-07-16T17:02:00.406905"
      }
    }
  }
  ```

### 6.6 Verify Cursor

- You can see the MCP server in the list of MCP servers in Cursor by navigating to `~/.cursor/mcp.json` and also by clicking on the settings icon on the top right and then clicking on `Tools & Integrations` or on the `MCP` tab

- *Generally restarting is not needed but if it is in loading state for a long time, please restart Cursor*

  ![cursor-mcp-running](./docs/images/cursor-mcp-running.png)

- Now you can chat with the MCP server.

  - **Example prompts:**

    - *(Click `Run Tool` when Cursor asks you to)*

    - `list all servers, get all tools available and echo test`
      - This uses a test MCP server `echo_server` which is in `bad_mcps/echo_mcp.py`

    ![cursor-mcp-chat](./docs/images/cursor-mcp-chat.png)

</details>

## 7. Edit the Gateway config as needed

<details>
<summary><strong>✂️ Edit Gateway Config </strong></summary>

- **Important:**

  - **We need to restart Claude Desktop after editing the config file**
  - **To make all new tools accessible, please use prompt "`list all servers, get all tools available`" for the MCP Client to discover all new tools. After this the MCP Client should be able to use all tools of the servers configured in the Gateway config file**

- You can add many MCP servers inside the `mcp_config` array of this gateway config

  - You can [look here for example servers](https://github.com/modelcontextprotocol/servers)

  - You can also try the [Enkrypt MCP Server](https://github.com/enkryptai/enkryptai-mcp-server)

  - Example:

      ```json
      {
        "common_mcp_gateway_config": {...},
        "mcp_configs": {
          "UNIQUE_MCP_CONFIG_ID": {
            "mcp_config_name": "default_config",
            "mcp_config": [
              {
                "server_name": "MCP_SERVER_NAME_1",
                "description": "MCP_SERVER_DESCRIPTION_1",
                "config": {
                  "command": "python/npx/etc.",
                  "args": [
                    "arg1", "arg2", ...
                  ],
                  "env": { "key": "value" }
                },
                // Set explicit tools to restrict access to only the allowed tools
                // Example: "tools": { "tool_name": "tool_description" }
                // Example: "tools": { "echo": "Echo a message" }
                // Or leave the tools empty {} to discover all tools dynamically
                "tools": {},
                "input_guardrails_policy": {...},
                "output_guardrails_policy": {...}
              },
              {
                "server_name": "MCP_SERVER_NAME_2",
                "description": "MCP_SERVER_DESCRIPTION_2",
                "config": {...},
                "tools": {},
                "input_guardrails_policy": {...},
                "output_guardrails_policy": {...}
              }
            ]
          },
          "UNIQUE_MCP_CONFIG_ID_2": {...}
        },
        "projects": {
          "UNIQUE_PROJECT_ID": {
            "project_name": "default_project",
            "mcp_config_id": "UNIQUE_MCP_CONFIG_ID",
            "users": [
              "UNIQUE_USER_ID"
            ],
            "created_at": "2025-01-01T00:00:00.000000"
          },
          "UNIQUE_PROJECT_ID_2": {...}
        },
        "users": {
          "UNIQUE_USER_ID": {
            "email": "default@example.com",
            "created_at": "2025-01-01T00:00:00.000000"
          },
          "UNIQUE_USER_ID_2": {...}
        },
        "apikeys": {
          "UNIQUE_GATEWAY_KEY": {
            "project_id": "UNIQUE_PROJECT_ID",
            "user_id": "UNIQUE_USER_ID",
            "created_at": "2025-01-01T00:00:00.000000"
          },
          "UNIQUE_GATEWAY_KEY_2": {...}
        }
      }
      ```

<br>
<details>
<summary><strong>⛩️ Gateway Config Schema</strong></summary>

- If you want a different set of MCP servers for a separate client/user, you can add a new `mcp_config` section to the config file. Also, you can run cli commands. See [CLI-Commands-Reference.md](./CLI-Commands-Reference.md) section `2. CONFIGURATION MANAGEMENT` for details

- Set `enkrypt_log_level` to `DEBUG` to get more detailed logs inside `common_mcp_gateway_config` part of the config file

  - This defaults to `INFO`

- Now, inside `mcp_configs` array, for each individual MCP config, you can set the following:

  - `server_name`: A name of the MCP server which we connect to

  - `description` (optional): A description of the MCP server

  - `config`: The config for the MCP server as instructed by the MCP server's documentation

    - Generally you have the below keys in the config:

      - `command`: The command to run the MCP server

      - `args`: The arguments to pass to the command

      - `env`: The environment variables to set for the command

  - `tools`: The tools exposed by the MCP server

    - Either set explicit tools to restrict access to only the allowed tools or **leave it empty `tools": {}` for the Gateway to discover all tools dynamically**

    - Tools need to be given a name and a description like `"tools": { "dummy_echo": "Echo a message" }`

</details>
<details>
<summary><strong>🔒 Optional Guardrails Schema</strong></summary>

- Get your `enkrypt_api_key` from [Enkrypt Dashboard](https://app.enkryptai.com/settings) and add it to `common_mcp_gateway_config` section of the config file

- `enkrypt_use_remote_mcp_config` is used to fetch MCP server config from Enkrypt server remotely *(Coming soon)*

  - Please use `false` for now

  - This enables you to configure and manage MCP gateway config in Enkrypt Dashboard in a centralized place *(Coming soon)*

- If you have any external cache server like KeyDB running, you can set `enkrypt_mcp_use_external_cache` to `true` in your `common_mcp_gateway_config`

  - Set other relevant keys related to cache in your `common_mcp_gateway_config`

- `enkrypt_tool_cache_expiration` (in hours) decides how long the tools discovered from the MCP servers are cached locally or in the external cache server

- `enkrypt_gateway_cache_expiration` (in hours) decides how long the gateway config is cached locally or in the external cache server. This is useful when we integrate this with Enkrypt Auth server *(Coming soon)*

- `enkrypt_async_input_guardrails_enabled`

  - `false` by default

  - **Async mode is not recommended for tools that perform actions which cannot be undone**

  - Because the tool call is made parallel to guardrails call, it can't be blocked if input guardrails violations are detected

  - Useful for servers that return just info without performing actions i.e., only read operations

- `enkrypt_async_output_guardrails_enabled` *(Coming soon)*

  - This makes output side guardrails calls asynchronously to save time

  - i.e., Guardrails detect call, relevancy check, adherence check, PII unredaction, etc. are made in parallel after getting the response from the MCP server

- **Inside each MCP server config, you can set the following:**

  - `input_guardrails_policy`: Use this if we plan to use Enkrypt Guardrails on input side

  - `policy_name`: Name of the guardrails policy that you have created in the Enkrypt App or using the API/SDK

  - `enabled`: Whether to enable guardrails on the input side or not. This is `false` in the example config file

  - `additional_config`: Additional config for the guardrails policy

    - `pii_redaction`: Whether to redact PII in the request sent to the MCP server or not

      - If `true`, this also auto unredacts the PII in the response from the MCP server

  - `block`: List of guardrails to block

    - Possible values in the array are:

      - `topic_detector, nsfw, toxicity, pii, injection_attack, keyword_detector, policy_violation, bias, sponge_attack`

      - `system_prompt_protection, copyright_protection` *(Coming soon)*

      - This is similar to our AI Proxy deployments config. [Refer to our docs](https://docs.enkryptai.com/deployments-api-reference/endpoint/add-deployment#body-input-guardrails-policy-block)

- `output_guardrails_policy`: Use this if we plan to use Enkrypt Guardrails on output side

  - `policy_name`: Name of the guardrails policy that you have created in the Enkrypt App or using the API/SDK

  - `enabled`: Whether to enable guardrails on the output side or not. This is `false` in the example config file

  - `additional_config`: Additional config for the guardrails policy

    - `relevancy`: Whether to check for relevancy of the response from the MCP server

    - `adherence`: Whether to check for adherence of the response from the MCP server

    - `hallucination`: Whether to check for hallucination in the response from the MCP server *(Coming soon)*

  - `block`: List of guardrails to block

    - Possible values in the array are:

      - All possible values in input block array plus `adherence, relevancy`

      - `system_prompt_protection, copyright_protection, hallucination` *(Coming soon)*

      - This is similar to our AI Proxy deployments config. [Refer to our docs](https://docs.enkryptai.com/deployments-api-reference/endpoint/add-deployment#body-output-guardrails-policy-block)

</details>
</details>

## 8. (Optional) Add GitHub MCP Server to the Gateway

<details>
<summary><strong>👨🏻‍💻 Configure GitHub </strong></summary>

- `GitHub MCP Server` needs `docker` to be installed. So, please install and have `docker` running on your machine before proceeding with the steps below

  - You can [download docker desktop from here](https://www.docker.com/products/docker-desktop/). Install and run it if you don't have it already

- [Create a personal access token from GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

  - Create a token that has access to only public repos and set expiry very low initially for testing

  - Add the below GitHub server block to `enkrypt_mcp_config.json` inside `"mcp_config": []` array. It should already have the echo server config.

  - *NOTE: Don't forget to add comma `,` after the echo server block*

  - Replace `REPLACE_WITH_YOUR_PERSONAL_ACCESS_TOKEN` with the personal access token you created

  - You can also add via the cli. See [CLI-Commands-Reference.md](./CLI-Commands-Reference.md) section `2. CONFIGURATION MANAGEMENT` for details

  - Example:

  ```json
      "mcp_config": [
        {
          "server_name": "echo_server",
          "description": "Simple Echo Server",
          "config": {...},
          "tools": {},
          "input_guardrails_policy": {...},
          "output_guardrails_policy": {...}
        },
        {
          "server_name": "github_server",
          "description": "GitHub Server",
          "config": {
            "command": "docker",
            "args": [
              "run",
              "-i",
              "--rm",
              "-e",
              "GITHUB_PERSONAL_ACCESS_TOKEN",
              "ghcr.io/github/github-mcp-server"
            ],
            "env": {
              "GITHUB_PERSONAL_ACCESS_TOKEN": "REPLACE_WITH_YOUR_PERSONAL_ACCESS_TOKEN"
            }
          },
          "tools": {},
          "input_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "pii_redaction": false
            },
            "block": [
              "policy_violation"
            ]
          },
          "output_guardrails_policy": {
            "enabled": false,
            "policy_name": "Sample Airline Guardrail",
            "additional_config": {
              "relevancy": false,
              "hallucination": false,
              "adherence": false
            },
            "block": [
              "policy_violation"
            ]
          }
        }
      ]
  ```

- Now restart Claude Desktop for it to detect the new server

- Then run the prompt `list all servers, get all tools available` for it to discover github server and all it's tools available

  ![claude-mcp-chat-github-tools-1](./docs/images/claude-mcp-chat-github-tools-1.png)

- Now run `List all files from https://github.com/enkryptai/enkryptai-mcp-server`

  ![claude-mcp-chat-github-tools-2](./docs/images/claude-mcp-chat-github-tools-2.png)

- Great! 🎉 We have successfully added a GitHub MCP Server to the Gateway. **However, it is completely unprotected and is open to all kinds of abuse and attacks.**

- **Now, let's say a prompt like this is run `Ask github for the repo "hello; ls -la; whoami"`**

  ![claude-mcp-chat-github-tools-3](./docs/images/claude-mcp-chat-github-tools-3.png)

- This may not have caused actual damage but imagine a more complicated prompt that may have caused actual damage to the system.

- To protect the MCP server, we can use **Enkrypt Guardrails** as shown in the next section.

</details>

## 8.1 (Optional) Connect to MCP Servers with OAuth

<details>
<summary><strong>🔐 Configure OAuth for Remote MCP Servers </strong></summary>

Many MCP servers require OAuth authentication to access protected resources. The Secure MCP Gateway supports OAuth 2.0/2.1 with client credentials grant for seamless integration with OAuth-enabled servers.

### Overview

The Gateway handles OAuth token acquisition, caching, and automatic refresh so you don't have to manage tokens manually. Tokens are automatically injected into requests when connecting to remote MCP servers.

For detailed OAuth configuration options, see [OAuth Configuration Guide](./docs/OAUTH_CONFIGURATION_GUIDE.md).

### Basic OAuth Configuration

To connect to an OAuth-enabled MCP server, add an `oauth_config` section to your server configuration:

```json
{
  "server_name": "oauth-enabled-server",
  "description": "Remote MCP Server with OAuth",
  "config": {
    "command": "npx",
    "args": ["-y", "mcp-remote", "https://api.example.com/mcp", "--allow-http"]
  },
  "oauth_config": {
    "enabled": true,
    "is_remote": true,
    "OAUTH_VERSION": "2.1",
    "OAUTH_GRANT_TYPE": "client_credentials",
    "OAUTH_CLIENT_ID": "your-client-id",
    "OAUTH_CLIENT_SECRET": "your-client-secret",
    "OAUTH_TOKEN_URL": "https://auth.example.com/oauth/token",
    "OAUTH_AUDIENCE": "https://api.example.com"
  },
  "tools": {},
  "enable_tool_guardrails": true,
  "input_guardrails_policy": {
    "enabled": false
  },
  "output_guardrails_policy": {
    "enabled": false
  }
}
```

### Key OAuth Fields

#### Core Configuration

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `enabled` | Yes | `false` | Enable OAuth for this server |
| `is_remote` | Recommended | Auto-detected | Set to `true` for remote servers, `false` for local servers |
| `OAUTH_VERSION` | No | `"2.1"` | OAuth version: `"2.0"` or `"2.1"` |
| `OAUTH_GRANT_TYPE` | No | `"client_credentials"` | OAuth grant type (currently only client credentials supported) |
| `OAUTH_CLIENT_ID` | Yes | - | Your OAuth client ID |
| `OAUTH_CLIENT_SECRET` | Yes | - | Your OAuth client secret |
| `OAUTH_TOKEN_URL` | Yes | - | Token endpoint URL (must be HTTPS for OAuth 2.1) |

#### Optional OAuth Parameters

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `OAUTH_AUDIENCE` | No | `null` | Intended audience for the token (aud claim) |
| `OAUTH_ORGANIZATION` | No | `null` | Organization ID (for multi-tenant OAuth providers) |
| `OAUTH_SCOPE` | No | `null` | Space-separated scopes (e.g., "read write") |
| `OAUTH_RESOURCE` | No | `null` | Resource indicator (RFC 8707) |
| `OAUTH_TOKEN_EXPIRY_BUFFER` | No | `300` | Seconds before token expiry to trigger refresh (default: 5 minutes) |
| `OAUTH_ADDITIONAL_PARAMS` | No | `{}` | Additional parameters to include in token requests (JSON object) |
| `OAUTH_CUSTOM_HEADERS` | No | `{}` | Custom HTTP headers for token requests (JSON object) |

#### Security & Authentication Settings

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `OAUTH_USE_BASIC_AUTH` | No | `true` | Use HTTP Basic Auth for client credentials (RFC 6749 §2.3.1) |
| `OAUTH_ENFORCE_HTTPS` | No | `true` | Enforce HTTPS for OAuth 2.1 compliance (set `false` only for local testing) |
| `OAUTH_TOKEN_IN_HEADER_ONLY` | No | `true` | Send token only in Authorization header (recommended) |
| `OAUTH_VALIDATE_SCOPES` | No | `true` | Verify returned token contains requested scopes |

#### Mutual TLS (mTLS) Configuration

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `OAUTH_USE_MTLS` | No | `false` | Enable mutual TLS (RFC 8705) for enhanced security |
| `OAUTH_CLIENT_CERT_PATH` | Conditional | `null` | Path to client certificate file (required if mTLS enabled) |
| `OAUTH_CLIENT_KEY_PATH` | Conditional | `null` | Path to client private key file (required if mTLS enabled) |
| `OAUTH_CA_BUNDLE_PATH` | No | `null` | Path to CA bundle for server certificate verification |

#### Token Revocation

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `OAUTH_REVOCATION_URL` | No | `null` | Token revocation endpoint URL (RFC 7009) |

### Testing with Echo OAuth Server

The Gateway includes a test echo server that demonstrates OAuth header injection. You can use it to verify OAuth is working correctly.

#### Step 1: Start the Echo OAuth Server

The echo OAuth server needs to run in HTTP mode to accept remote connections:

**macOS/Linux:**

```bash
# Export the environment variable
export MCP_HTTP_MODE=true

# Start the server
python src/secure_mcp_gateway/bad_mcps/echo_oauth_mcp.py
```

**Windows (PowerShell):**

```powershell
# Set the environment variable
$env:MCP_HTTP_MODE = "true"

# Start the server
python src/secure_mcp_gateway/bad_mcps/echo_oauth_mcp.py
```

**Windows (Command Prompt):**

```cmd
# Set the environment variable
set MCP_HTTP_MODE=true

# Start the server
python src/secure_mcp_gateway/bad_mcps/echo_oauth_mcp.py
```

The server will start on `http://localhost:8001/mcp/` and print OAuth-related headers whenever tools are called.

#### Step 2: Add Echo OAuth Server to Gateway Config

Add this configuration to your `enkrypt_mcp_config.json` in the `mcp_config` array:

```json
{
  "server_name": "echo_oauth_server",
  "description": "Echo Server with OAuth Testing",
  "config": {
    "command": "npx",
    "args": [
      "-y",
      "mcp-remote",
      "http://localhost:8001/mcp/",
      "--allow-http"
    ]
  },
  "oauth_config": {
    "enabled": true,
    "is_remote": true,
    "OAUTH_VERSION": "2.0",
    "OAUTH_GRANT_TYPE": "client_credentials",
    "OAUTH_CLIENT_ID": "test-client-id",
    "OAUTH_CLIENT_SECRET": "test-client-secret",
    "OAUTH_TOKEN_URL": "https://auth.example.com/oauth/token",
    "OAUTH_ENFORCE_HTTPS": false
  },
  "tools": {},
  "enable_tool_guardrails": false,
  "input_guardrails_policy": {
    "enabled": false
  },
  "output_guardrails_policy": {
    "enabled": false
  }
}
```

**Note:** `OAUTH_ENFORCE_HTTPS: false` is set only for local testing. Always use HTTPS in production!

#### Step 3: Test OAuth Token Injection

1. Restart Claude Desktop (or your MCP client) to pick up the new server configuration

2. Use the prompt: `list all servers and discover tools from echo_oauth_server`

3. Call the echo tool: `call the echo tool from echo_oauth_server with message "test oauth"`

4. Check the echo server terminal output - you should see OAuth headers being printed:

```
================================================================================
🔐 OAuth HTTP Headers Check (Remote Mode)
================================================================================
  ✅ AUTHORIZATION: Bearer <token>...
  ❌ X-OAUTH-TOKEN: Not set
  ❌ X-ACCESS-TOKEN: Not set

📋 All Request Headers:
  authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  content-type: application/json
  user-agent: python-requests/2.31.0
================================================================================
```

This confirms the OAuth token is being automatically acquired and injected into the Authorization header.

### OAuth Token Flow

1. **First Request**: Gateway acquires token from OAuth provider
2. **Caching**: Token is cached with expiration tracking
3. **Token Injection**:
   - **Remote servers**: Token added as `Authorization: Bearer <token>` header via `mcp-remote --header` argument
   - **Local servers**: Token available in environment variables (ENKRYPT_ACCESS_TOKEN, etc.)
4. **Auto-refresh**: Token refreshed 5 minutes before expiry (configurable)

### Advanced Features

- **Mutual TLS (mTLS)**: Enhanced security with client certificates
- **Token Revocation**: Programmatically revoke tokens (RFC 7009)
- **Scope Validation**: Verify returned token has requested scopes
- **Custom Headers**: Add custom HTTP headers to token requests
- **Metrics**: Track token acquisition success/failure, cache hit ratio

See the [OAuth Configuration Guide](./docs/OAUTH_CONFIGURATION_GUIDE.md) for complete documentation.

### Troubleshooting

**OAuth token request failed:**
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check TOKEN_URL is reachable
- Ensure HTTPS is used (or set `OAUTH_ENFORCE_HTTPS: false` for testing)

**Token not appearing in requests:**
- Confirm `is_remote: true` for remote servers
- Check server logs for OAuth acquisition messages
- Enable debug logging: `"enkrypt_log_level": "DEBUG"`

**Echo server not receiving headers:**
- Ensure `MCP_HTTP_MODE=true` environment variable is set
- Verify server is running on http://localhost:8001/mcp/

</details>

## 9. (Optional) Protect GitHub MCP Server and Test Echo Server

<details>
<summary><strong>🎁 Protect with Enkrypt Guardrails for FREE </strong></summary>
<br>
<details>
<summary><strong>8.1 🌐 Create a Guardrail in Enkrypt App </strong></summary>
<br>

- You can use a prompt to generate rules or generate a PDF file while you can then paste or upload while creating a policy in the App

<br>
<details>
<summary><strong>8.1.1 🔍 Rules to copy </strong></summary>
<br>

```text

1. MCP-Specific Security Policies
Scan all tool descriptions for hidden instructions/malicious patterns.

Authenticate MCP servers with cryptographic verification.

Lock and pin tool versions to prevent rug-pull attacks.

Enforce isolation between MCP servers to avoid interference.

Restrict GitHub MCP access to specific repositories and users.

2. Code Filtering and Prohibited Patterns
Block known malicious code patterns (e.g., buffer overflows, SQL injection).

Detect malware signatures (e.g., keylogger, trojan).

Prevent crypto mining code.

Identify network attack patterns (e.g., DDoS, botnet).

Block privilege escalation code (e.g., root exploits).

3. Repository Access Control
Enforce role-based read access for private repositories.

Enable strict content filtering for all access types.

Mandate audit logging for private repositories.

Quarantine access to sensitive repositories.

4. AI-Specific Guardrails
Detect tool poisoning via hidden tags and file access commands.

Monitor behavior for file access and network activity.

Require explicit UI approval for suspicious tools.

Protect against prompt injection in GitHub issues.

Block PRs that expose private repo data.

Quarantine suspicious GitHub issues.

5. RADE (Retrieval-Agent Deception) Mitigation
Scan retrieved content for embedded commands.

Validate document integrity and modification timestamps.

Sandbox retrieved content to prevent auto-execution.

6. Input Validation
Limit prompt length (max 4096 tokens).

Block forbidden keywords (e.g., "ignore previous instructions").

Detect encoded/injection patterns (base64, hex, unicode).

7. Model Behavior Constraints
Limit code generation by complexity and size.

Restrict certain languages (e.g., shell scripts, assembly).

Monitor API/system calls and network activity.

Enforce strict context boundaries across repositories.

```

</details>
<br>
<details>
<summary><strong>9.1.2 💡 Prompt used to generate the rules </strong></summary>
<br>

- `Give numbered list of security rules in plain text for configuring AI guardrails for a GitHub server on the rules and policies it needs to follow to prevent malicious use of the GitHub services`

- Then say `Research latest GitHub MCP hacks and abuses people are trying and update the rules to prevent those. Keep research to the most severe topics`

- Then say `Only keep essential security rules to reduce size. Remove unwanted sections like post incident, compliance, audit, etc which cannot be used while prevention`

- Then you can copy paste the rules while creating the policy

</details>
<br>

- Go to [Enkrypt App](https://app.enkryptai.com) and login with either OTP or Google or Microsoft account

- Click on `Policies`

  ![enkrypt-github-guardrail-1](./docs/images/enkrypt-github-guardrail-1.png)

- Click on `Add new policy`

  ![enkrypt-github-guardrail-2](./docs/images/enkrypt-github-guardrail-2.png)

- Name it `GitHub Safe Policy` and paste the policy rules and click `Save`

  ![enkrypt-github-guardrail-3](./docs/images/enkrypt-github-guardrail-3.png)

- This is how a saved policy looks like with the rules applied for `Policy violation` Guardrails

  ![enkrypt-github-guardrail-4](./docs/images/enkrypt-github-guardrail-4.png)

- Now navigate back to home or hover over left sidebar and click `Guardrails`

- Click on `Add New Guardrail` button on the top right

  ![enkrypt-app-add-guardrail-button](./docs/images/enkrypt-app-add-guardrail-button.png)

- Name it `GitHub Guardrail`, toggle `Injection Attack` OFF

  ![enkrypt-app-add-guardrail-add-1](./docs/images/enkrypt-app-add-guardrail-add-1.png)

- Scroll down on `Configure Guardrails` side panel and toggle `Policy Violation` ON, select the newly created policy and tick `Need Explanation` if needed

  ![enkrypt-app-add-guardrail-add-2](./docs/images/enkrypt-app-add-guardrail-add-2.png)

- Now, click on `Save` button on the bottom right to save the guardrail

  ![enkrypt-app-add-guardrail-add-3](./docs/images/enkrypt-app-add-guardrail-add-3.png)

- We can see the newly added guardrail in the list of guardrails

  ![enkrypt-app-add-guardrail-add-4](./docs/images/enkrypt-app-add-guardrail-add-4.png)

</details>
<details>
<summary><strong>9.2 🔑 Get Enkrypt API Key </strong></summary>
<br>

- Now, we need get out FREE API Key from Enkrypt App. Hover over the left sidebar for it to expand and click on `Settings`

  - You can also directly navigate to [https://app.enkryptai.com/settings](https://app.enkryptai.com/settings)

  ![enkrypt-app-settings-1](./docs/images/enkrypt-app-settings-1.png)

- Now click on the `Copy` icon next to your obfuscated API Key to copy the key to your clipboard as highlighted in the screenshot below

  ![enkrypt-app-settings-2](./docs/images/enkrypt-app-settings-2.png)

</details>
<details>
<summary><strong>9.3 🔑 Add API Key and the Guardrail to Config File </strong></summary>
<br>

- Now we have everything we need from the App. Let's add the API Key to the `enkrypt_mcp_config.json` file

- Open the `enkrypt_mcp_config.json` file from `~/.enkrypt/enkrypt_mcp_config.json` on macOS or `%USERPROFILE%\.enkrypt\enkrypt_mcp_config.json` on Windows

  - *If you ran docker command to install the Gateway, the config file will be in `~/.enkrypt/docker/enkrypt_mcp_config.json` on macOS and `%USERPROFILE%\.enkrypt\docker\enkrypt_mcp_config.json` on Windows*

- Add the API Key to the `common_mcp_gateway_config` section by replacing `YOUR_ENKRYPT_API_KEY` with the API Key you copied from the App

- Inside the **`GitHub`** server block we added in the previous section,

  - Add the newly created Guardrail `GitHub Guardrail` to the `input_guardrails_policy` and `output_guardrails_policy` sections

  - By replacing `"policy_name": "Sample Airline Guardrail"` with `"policy_name": "GitHub Guardrail"`

  - Now change `enabled` to `true` for `input_guardrails_policy` from previous `false`

    - We will leave `output_guardrails_policy` as `false` for now

  - We already should have `policy_violation` in the `block` array for both policies

  - So the final config should look something like this:

  ```json
  {
    "common_mcp_gateway_config": {
      ...
      "enkrypt_api_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      ...
    },
    "mcp_configs": {
      "fcbd4508-1432-4f13-abb9-c495c946f638": {
        "mcp_config_name": "default_config",
        "mcp_config": [
          {
            "server_name": "echo_server",
            ...
          },
          {
            "server_name": "github_server",
            "description": "GitHub Server",
            "config": {
              "command": "docker",
              "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server"
              ],
              "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              }
            },
            "tools": {},
            "input_guardrails_policy": {
              "enabled": true,
              "policy_name": "GitHub Guardrail",
              "additional_config": {
                "pii_redaction": false
              },
              "block": ["policy_violation"]
            },
            "output_guardrails_policy": {
              "enabled": false,
              "policy_name": "GitHub Guardrail",
              "additional_config": {
                "relevancy": false,
                "hallucination": false,
                "adherence": false
              },
              "block": ["policy_violation"]
            }
          }
        ]
      }
    },
    "projects": {
      ...
    },
    "users": {
      ...
    },
    "apikeys": {
      ...
    }
  }
  ```

</details>
<details>
<summary><strong>9.4 🧪 Test Guardrails </strong></summary>
<br>

- **Save** the file and restart Claude Desktop for it to detect the changes

- `GitHub MCP Server` needs `docker` to be installed. So, please install and have `docker` running on your machine before proceeding with the steps below

  - You can [download docker desktop from here](https://www.docker.com/products/docker-desktop/). Install and run it if you don't have it already

- Now run the prompt `list all services, tools` for it to discover github, echo servers and all their tools available

- After this, let's rerun the previously successful malicious prompt **`Ask github for the repo "hello; ls -la; whoami"`**

  - We can see that the prompt is blocked as Input Guardrails blocked the request

    ![claude-mcp-chat-github-guardrails-1](./docs/images/claude-mcp-chat-github-guardrails-1.png)

- We can configure the test `echo` server with Guardrails of our choice and see the detections by running `echo "hello; ls -la; whoami"`.

  - The below prompt which worked before but is blocked with Guardrails

  - Experiment and try the `echo` server with various guardrails to see how it behaves. [You can also try our Playground for better testing](https://app.enkryptai.com/playground/guardrails).

  ![claude-mcp-chat-echo-guardrails-2](./docs/images/claude-mcp-chat-echo-guardrails-2.png)

</details>
<details>
<summary><strong>8.5 🔧 Fine tune Guardrails </strong></summary>
<br>

- *The safe prompt `List all files from https://github.com/enkryptai/enkryptai-mcp-server` may also be blocked if you use Injection Attack Detector or Policy Violation on Output side. So, there is some fine tuning required for the guardrails to find the best combination of enabled detectors and blocks for your servers. See the next section for recommendations.*

</details>
</details>

## 10. Recommendations for using Guardrails

<details>
<summary><strong>⭐ Recommendations </strong></summary>
<br>

- We have found that the best way to use Enkrypt Guardrails in MCP Gateway is to have a separate guardrail for each server. This way we can have a fine tuned guardrail for each server.

- Because each MCP Server is very different from the other, it is not possible to have a single guardrail that works for all servers.

- Some may need `Toxicity Detector`, some `NSFW Detector`, some `Injection Attack Detector`, some `Keyword Detector`, some `Policy Violation`, some may need `Relevancy` detector, some may need `Adherence` detector, etc.

- Some may need a combination of these detectors to work together to block malicious requests.

- Some may need Guardrails on the input side, some on the output and some may need both to be applied.

- See our docs for details on [various detectors available.](https://docs.enkryptai.com/guardrails-api-reference/Prompt_Injection)

- Hence, have separate guardrails for each server and experiment with the best combination of detectors and blocks for each server that blocks malicious requests but allows legitimate requests to pass through.

- Try our `Policy Violation` detector with your own custom policy which details what is allowed and what is not. This may be the best way for your use case.

<details>
<summary><strong>🚨 Try Policy Violation </strong></summary>
<br>

- You can navigate to the [Enkrypt App Homepage](https://app.enkryptai.com), login and Click on `Policies` to create your own custom policy.

  - This accepts text as well as PDF file as input so create a file with all the rules you want to apply to your MCP server and upload it

  - Once created, you can use it while configuring the Guardrail like we say with `GitHub Guardrail` in the previous section

  ![enkrypt-app-homepage-policies](./docs/images/enkrypt-app-homepage-policies.png)

</details>
</details>

## 11. Other Tools Available

<details>
<summary><strong>💾 Cache Management </strong></summary>
<br>
<details>
<br>
<summary><strong>10.1 📊 Get Cache Status </strong></summary>

- The Gateway can give the summary of it's cache status by looking at the local/external cache server

- This is useful to debug issues if for example a tool was updated remotely by a server but the Gateway is not aware of it yet

  ![claude-mcp-chat-get-cache-status](./docs/images/claude-mcp-chat-get-cache-status.png)

</details>
<details>
<summary><strong>10.2 🧹 Clear Cache </strong></summary>

- The Gateway can clear it's cache from local/external cache server

- This is useful to clear the cache if for example a tool was updated remotely by a server but the Gateway is not aware of it yet

- You can either clear all cache or specific cache by providing the `server_name`

  - Example: `clear cache for echo_server`

- You can also clear all cache or just the gateway cache or just the server cache

  - Example: `clear all cache`, `clear just gateway cache`, `clear server cache for echo_server`, `Clear all server cache`

  ![claude-mcp-chat-clear-cache](./docs/images/claude-mcp-chat-clear-cache.png)

</details>
</details>

## 12. Deployment patterns

1. [Local Gateway, Local Guardrails and Local MCP Server](#111-local-gateway-local-guardrails-and-local-mcp-server)

2. [Local Gateway, Local MCP Server with Remote Guardrails](#112-local-gateway-local-mcp-server-with-remote-guardrails)

3. [Local Gateway with Remote MCP Server and Remote Guardrails](#113-local-gateway-with-remote-mcp-server-and-remote-guardrails)

4. [Remote Gateway, Remote MCP Server and Remote Guardrails](#114-remote-gateway-remote-mcp-server-and-remote-guardrails)

### 12.1 Local Gateway, Local Guardrails and Local MCP Server

![Local Gateway with Local Guardrails Flow](./docs/images/enkryptai-apiaas-MCP%20Gateway%20All%20Local.drawio.png)

### 12.2 Local Gateway, Local MCP Server with Remote Guardrails

![Local Gateway with Remote Guardrails Flow](./docs/images/enkryptai-apiaas-MCP%20Gateway%20Local.drawio.png)

### 12.3 Local Gateway with Remote MCP Server and Remote Guardrails

![Local Gateway with Remote Guardrails and Remote MCP Server Flow](./docs/images/enkryptai-apiaas-MCP%20Gateway%20Local%20with%20Remote.drawio.png)

### 12.4 Remote Gateway, Remote MCP Server and Remote Guardrails

![Remote Gateway with Remote Guardrails and Remote MCP Server Flow](./docs/images/enkryptai-apiaas-MCP%20Gateway%20Full%20Remote.drawio.png)

## 13. Uninstall the Gateway

<details>
<summary><strong>🗑️ Uninstall the Gateway </strong></summary>

- To remove the Gateway from any MCP client, just remove the MCP server block `"Enkrypt Secure MCP Gateway": {...}` from the client's config file.

  - Restart the MCP client to apply the changes for some clients like Claude Desktop. Cursor does not require a restart.

- To uninstall the pip package, run the following command:

  ```bash
  pip uninstall secure-mcp-gateway
  ```

</details>

## 14. Troubleshooting

<details>
<summary><strong>🕵 Troubleshooting </strong></summary>

- If any calls fail in the client, please look at the mcp logs of the respective client

  - [See this for Claude logs location](https://modelcontextprotocol.io/docs/tools/debugging#viewing-logs)

    - Example 🍎 Linux/macOS log path: `~/Library/Logs/Claude/mcp-server-Enkrypt Secure MCP Gateway.log`
    - Example 🪟 Windows log path: `%USERPROFILE%\AppData\Roaming\Claude\logs\mcp-server-Enkrypt Secure MCP Gateway.log`

  - [See this discussion for Cursor logs](https://forum.cursor.com/t/where-can-we-find-mcp-error-log/74719)

- If you see errors like `Exception: unhandled errors in a TaskGroup (1 sub-exception)` then maybe the MCP server the gateway is trying to use is not running.
  - So, please make sure the file it is trying to access is available
  - Any pre-requisites for the MCP server to run are met like `docker` running, etc.

- If we need more detailed logs, please set the `enkrypt_log_level` to `debug` in the `enkrypt_mcp_config.json` file and restart the MCP client.

### 14.1 OpenTelemetry Troubleshooting

1. **SSL Handshake Errors**

   If you see SSL errors like:

   ```bash
   SSL_ERROR_SSL: error:100000f7:SSL routines:OPENSSL_internal:WRONG_VERSION_NUMBER
   ```

   Solution: Add `insecure=True` to the OTLP exporter configuration in `telemetry.py`

2. **No Logs in Loki**

   - Verify OTLP collector is running:

     ```bash
     docker logs secure-mcp-gateway-otel-collector-1
     ```

   - Check collector config in `otel_collector/otel-collector-config.yaml`

   - Verify Loki is receiving data:

     ```bash
     curl -G -s "http://localhost:3100/loki/api/v1/query" --data-urlencode 'query={job="enkrypt"}'
     ```

3. **Missing Metrics**

   - Check OTLP collector metrics pipeline:

     ```bash
     curl http://localhost:8888/metrics
     ```

   - Verify metrics in collector logs:

     ```bash
     docker logs secure-mcp-gateway-otel-collector-1 | grep "metrics"
     ```

4. **Docker Issues**

   ```bash
   # Restart the stack
   docker-compose down
   docker-compose up -d

   # Check individual service logs
   docker logs <service-name>
   ```

</details>

## 15. Known Issues being worked on

- Output guardrails are not being applied to non-text tool results. Support for other media types like images, audio, etc. is coming soon.

## 16. Known Limitations

- The Gateway does not support a scenario where the Gateway is deployed remotely but the MCP server is deployed locally (without being exposed to the internet). This is because the Gateway needs to know the MCP server's address to forward requests to it.

## 17. Contribute

- Look at the `TODO` file for the current work in progress and yet to be implemented features

- Install the gateway locally to test your changes
  - by following the [Git clone steps](#42-local-installation-with-git-clone)
  - or build it using `python -m build`, activate the venv and install using `pip install .`

- Report or fix any bugs you encounter 😊

## 18. License

### 18.1 Enkrypt AI MCP Gateway Core

This project's core functionality is licensed under the MIT License.

<!-- In addition to the MIT License, the following additional terms apply:

- You can freely use, modify, and distribute this software as part of your commercial product

- You can use this as part of your commercial product if your product is not an MCP gateway or gateway-based service

- You cannot sell this gateway as a standalone product -->

For the full license text, see the `LICENSE.txt` file in this repository.

### 18.2 Enkrypt AI Guardrails, Logo, and Branding

© 2025 Enkrypt AI. All rights reserved.

Enkrypt AI software is provided under a proprietary license. Unauthorized use, reproduction, or distribution of this software or any portion of it is strictly prohibited.

Terms of Use: [https://www.enkryptai.com/terms-and-conditions](https://www.enkryptai.com/terms-and-conditions)

Privacy Policy: [https://app.enkryptai.com/privacy-policy](https://app.enkryptai.com/privacy-policy)

Enkrypt AI and the Enkrypt AI logo are trademarks of Enkrypt AI, Inc.

[Go to top](#enkrypt-ai-secure-mcp-gateway)
