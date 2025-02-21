# Argo Proxy Project

This project is a proxy application that forwards requests to an ARGO API and optionally converts the responses to be compatible with OpenAI's API format.

## Table of Contents

- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Endpoints](#endpoints)
- [Models](#models)
- [Examples](#examples)

## Folder Structure

```
$ tree .
.
├── app.py
├── argoproxy
│   ├── chat.py
│   ├── completions.py
│   ├── config.py
│   ├── embed.py
│   ├── extras.py
│   └── utils.py
├── compose.yaml
├── config.yaml
├── examples
│   ├── chat_completions_example.py
│   ├── chat_example.py
│   ├── embedding_example.py
│   ├── o1-example.py
│   └── openai_o1_chat_example.py
├── README.md
├── requirements.txt
└── run_app.sh

2 directories, 17 files
```

## Prerequisites

- Python 3.8 or higher

## Configuration

The application is configured using a `config.yaml` file. This file contains settings such as the ARGO API URLs, port number, and logging behavior. Below is a breakdown of the configuration options:

### Configuration Options

- **`port`**: The port number on which the application will listen. Default is `44497`.
- **`argo_url`**: The URL of the ARGO API for chat and completions. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"`.
- **`argo_embedding_url`**: The URL of the ARGO API for embeddings. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"`.
- **`user`**: The user name to be used in the requests. Default is `"cels"`.
- **`verbose`**: A boolean flag to control whether to print input and output for debugging. Default is `true`.
- **`num_workers`**: The number of worker processes for Gunicorn. Default is `5`.
- **`timeout`**: The timeout for requests in seconds. Default is `600`.

### Example `config.yaml`

```yaml
port: 44497
argo_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
argo_embedding_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"
user: "cels"
verbose: true
num_workers: 5
timeout: 600
```

## Running the Application

1. **Install Dependencies**:
   Ensure you have Python 3.8 or higher installed. Install the required packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Use the provided `run_app.sh` script to start the application. By default, the script looks for a `config.yaml` file in the current directory. You can optionally specify a custom path to the configuration file as an argument:

   ```bash
   ./run_app.sh /path/to/config.yaml
   ```

   If no path is provided, the script will use the default `config.yaml` file in the current directory:

   ```bash
   ./run_app.sh
   ```

## Endpoints

The application provides the following endpoints:

- **`/v1/chat`**: Directly proxies requests to the ARGO API.
- **`/v1/chat/completions`**: Proxies requests to the ARGO API and converts the response to OpenAI-compatible format.
- **`/v1/completions`**: Proxies requests to the ARGO API and converts the response to OpenAI-compatible format (legacy).
- **`/v1/embeddings`**: Proxies requests to the ARGO Embedding API.
- **`/v1/models`**: Returns a list of available models in OpenAI-compatible format.
- **`/v1/status`**: Returns a simple "hello" response from GPT-4o.

## Models

This application provides proxy to the following models. You can call the models via either the argo original name or argo-proxy name.

### chat models

| Original ARGO Model Name | Argo Proxy Name            |
| ------------------------ | -------------------------- |
| `gpt35`                  | `argo:gpt-3.5-turbo`       |
| `gpt35large`             | `argo:gpt-3.5-turbo-16k`   |
| `gpt4`                   | `argo:gpt-4`               |
| `gpt4large`              | `argo:gpt-4-32k`           |
| `gpt4turbo`              | `argo:gpt-4-turbo-preview` |
| `gpt4o`                  | `argo:gpt-4o`              |
| `gpto1preview`           | `argo:gpt-o1-preview`      |
| `gpto1mini`              | `argo:gpt-o1-mini`         |

### embedding models

| Original ARGO Model Name | Argo Proxy Name               |
| ------------------------ | ----------------------------- |
| `ada002`                 | `argo:text-embedding-ada-002` |
| `v3small`                | `argo:text-embedding-3-small` |
| `v3large`                | `argo:text-embedding-3-large` |

## Examples

### Chat Completion Example

For an example of how to use the `/v1/chat/completions` endpoint, see the [ `chat_example.py` ](examples/chat_completions_example.py) file.

### Embedding Example

For an example of how to use the `/v1/embeddings` endpoint, see the [ `embedding_example.py` ](examples/embedding_example.py) file.

### o1 chat Example

For an example of how to use the `/v1/chat` endpoint with the `argo:gpt-o1-mini` model, see the [ `o1-example.py` ](examples/o1-example.py) file.

### OpenAI Client Example

## For an example of how to use the `/v1/chat/completions` endpoint with the OpenAI client, see the [ `openai_o1_chat_example.py` ](examples/openai_o1_chat_example.py) file.

### **Changes Made**

1. Added the **Configuration** section with a detailed explanation of the `config.yaml` file and its options.
2. Included an example `config.yaml` file for reference.
3. Ensured the **Configuration** section is properly linked in the Table of Contents.
