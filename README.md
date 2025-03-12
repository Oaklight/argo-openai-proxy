# Argo Proxy Project

This project is a proxy application that forwards requests to an ARGO API and optionally converts the responses to be compatible with OpenAI's API format. You can couple it with [autossh-tunnel-dockerized](https://github.com/Oaklight/autossh-tunnel-dockerized) or other secure connection tool.

## NOTICE OF USAGE
The machine or server making the API calls to Argo must be connected to Argonne internal network or through VPN on an Argonne-managed computer if you are working off-site. Meaning your instance of argo proxy should always be on premise at some Argonne Machine.
The software is provided as is, without any warranties or guarantees of any kind, either express or implied. By using this software, you agree that the authors, contributors, and any affiliated organizations shall not be held liable for any damages, losses, or issues arising from its use. This includes, but is not limited to, direct, indirect, incidental, consequential, or punitive damages. You are solely responsible for ensuring that the software meets your requirements and for any outcomes resulting from its use.

## Table of Contents

- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Endpoints](#endpoints)
- [Models](#models)
- [Examples](#examples)
- [Bug reports and Contributions](#bug-reports-and-contributions)

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
├── config.yaml
├── examples
│   ├── chat_completions_example.py
│   ├── chat_completions_example_stream.py
│   ├── chat_example.py
│   ├── chat_example_stream.py
│   ├── completions_example.py
│   ├── completions_example_stream.py
│   ├── embedding_example.py
│   ├── openai_chat_completions_example_stream.py
│   ├── openai_completions_example_stream.py
│   ├── problematic_prompt_for_o1.py
│   ├── pyclient_o1_chat_example.py
│   └── results_compare
│       ├── argo_chunk
│       ├── chat_completions
│       │   ├── my_chunk
│       │   ├── openai_chunk
│       │   └── siliconflow_chunk
│       ├── completions
│       │   ├── my_chunk
│       │   ├── openai_chunk
│       │   └── siliconflow_chunk
│       └── my_chunk
├── __pycache__
│   └── app.cpython-310.pyc
├── README.md
├── requirements.txt
└── run_app.sh

6 directories, 31 files
```

## Prerequisites

- Python 3.10 or higher

## Configuration

The application is configured using a `config.yaml` file. This file contains settings such as the ARGO API URLs, port number, and logging behavior. Below is a breakdown of the configuration options:

### Configuration Options

- **`port`**: The port number on which the application will listen. Default is `44497`.
- **`argo_url`**: The URL of the ARGO API for chat and completions. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"`.
- **`argo_stream_url`**: The URL of the ARGO API for stream chat and completions. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/steamchat/"`.
- **`argo_embedding_url`**: The URL of the ARGO API for embeddings. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"`.
- **`user`**: The user name to be used in the requests. Default is `"cels"`.
- **`verbose`**: A boolean flag to control whether to print input and output for debugging. Default is `true`.
- **`num_workers`**: The number of worker processes for Gunicorn. Default is `5`.
- **`timeout`**: The timeout for requests in seconds. Default is `600`.

### Example `config.yaml`

```yaml
# use production url as much as you can.
port: 44497
argo_url: "https://apps.inside.anl.gov/argoapi/api/v1/resource/chat/"
argo_stream_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
argo_embedding_url: "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
user: "cels" # you should replace it with your username
verbose: true
num_workers: 5
timeout: 600 # in seconds
```

## Running the Application

1. **Install Dependencies**:
   Ensure you have Python 3.10 or higher installed. Install the required packages using pip:

   ```bash
   # recommend to use `conda/mamba/venv` to manage argo specific environment
   # you can use `screen` to run it in background
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Use the provided `run_app.sh` script to start the application. By default, the script looks for a `config.yaml` file in the current directory. You can optionally specify a custom path to the configuration file as an argument:

   ```bash
   ./run_app.sh /path/to/config.yaml
   ```

   If no path is provided, the script will use the default [`config.yaml`](./config.yaml) file in the project root directory:

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

For an example of how to use the `/v1/chat/completions`, /v1/completions`, /v1/chat` endpoint, see the followings:
- [ `chat_completions_example.py` ](examples/chat_completions_example.py)
- [ `chat_completions_example_stream.py` ](examples/chat_completions_example_stream.py)
- [ `completions_example.py` ](examples/completions_example.py)
- [ `completions_example_stream.py` ](examples/completions_example_stream.py)
- [ `chat_example.py` ](examples/chat_example.py)
- [ `chat_example_stream.py` ](examples/chat_example_stream.py) 

### Embedding Example

For an example of how to use the `/v1/embeddings` endpoint, see the [ `embedding_example.py` ](examples/embedding_example.py) file.

### o1 chat Example

For an example of how to use the `/v1/chat` endpoint with the `argo:gpt-o1-mini` model, see the [ `o1_chat_example.py` ](examples/o1_chat_example.py) file.

### OpenAI Client Example

For an example of how to use the `/v1/chat/completions` endpoint with the OpenAI client, see the [ `openai_o1_chat_example.py` ](examples/o1_chat_example_pyclient.py) file.

## Bug reports and Contributions

This project is made during my spare time, so there for sure are bugs and issues. <br>
If you encounter any or have suggestions for improvements, please [open an issue](https://github.com/Oaklight/argo-proxy/issues/new) or [submit a pull request](https://github.com/Oaklight/argo-proxy/compare). <br>
Your contributions are highly appreciated!