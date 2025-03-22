# Argo Proxy Project

This project is a proxy application that forwards requests to an ARGO API and optionally converts the responses to be compatible with OpenAI's API format. It can be used in conjunction with [autossh-tunnel-dockerized](https://github.com/Oaklight/autossh-tunnel-dockerized) or other secure connection tools.

## Notice of Usage

The machine or server making API calls to Argo must be connected to the Argonne internal network or through a VPN on an Argonne-managed computer if you are working off-site. Your instance of the argo proxy should always be on-premise at an Argonne machine. The software is provided "as is," without any warranties. By using this software, you accept that the authors, contributors, and affiliated organizations will not be liable for any damages or issues arising from its use. You are solely responsible for ensuring the software meets your requirements.

## Table of Contents

- [Deployment](#deployment)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
  - [Endpoints](#endpoints)
  - [Models](#models)
  - [Examples](#examples)
- [Folder Structure](#folder-structure)
- [Bug Reports and Contributions](#bug-reports-and-contributions)

## Deployment

### Prerequisites

- Python 3.10 or higher is required.

### Configuration

The application is configured using a `config.yaml` file. This file contains settings like the ARGO API URLs, port number, and logging behavior.

#### Configuration Options

- **`port`**: Port number the application listens to. Default is `44497`.
- **`argo_url`**: URL of the ARGO API for chat/completions. Default: `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"`.
- **`argo_stream_url`**: URL for stream chat/completions. Default: `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/steamchat/"`.
- **`argo_embedding_url`**: URL for embeddings. Default: `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"`.
- **`user`**: Username for requests. Default: `"cels"`.
- **`verbose`**: Flag for debugging. Default: `true`.
- **`num_workers`**: Number of worker processes for Gunicorn. Default: `5`.
- **`timeout`**: Default request timeout in seconds. Default: `600`. This value can be overridden by providing a `timeout` parameter in the request or via the OpenAI client.

#### Example `config.yaml`

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

### Running the Application

1. **Install Dependencies**:
   Ensure Python 3.10 or higher is installed. Install required packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Use `run_app.sh` to start. It defaults to `config.yaml` in the current directory or specify a custom config:

   ```bash
   ./run_app.sh /path/to/config.yaml
   ```

   Without a path, it uses the default `config.yaml`:

   ```bash
   ./run_app.sh
   ```

## Usage

### Endpoints

#### OpenAI Compatible

These endpoints convert responses from the ARGO API to be compatible with OpenAI's format:

- **`/v1/chat/completions`**: Converts ARGO chat/completions responses to OpenAI-compatible format.
- **`/v1/completions`**: Legacy API for conversions to OpenAI format.
- **`/v1/embeddings`**: Accesses ARGO Embedding API with response conversion.
- **`/v1/models`**: Lists available models in OpenAI-compatible format.

#### Not OpenAI Compatible

These endpoints interact directly with the ARGO API and do not convert responses to OpenAI's format:

- **`/v1/chat`**: Proxies requests to the ARGO API without conversion.
- **`/v1/status`**: Responds with a simple "hello" from GPT-4o, knowing it is alive.

#### Timeout Override

You can override the default timeout with a `timeout` parameter in your request.

Details of how to make such override in different query flavors: [Timeout Override Examples](timeout_examples.md)

### Models

#### Chat Models

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
| `gpto3mini`              | `argo:gpt-o3-mini`         |

#### Embedding Models

| Original ARGO Model Name | Argo Proxy Name               |
| ------------------------ | ----------------------------- |
| `ada002`                 | `argo:text-embedding-ada-002` |
| `v3small`                | `argo:text-embedding-3-small` |
| `v3large`                | `argo:text-embedding-3-large` |

### Examples

#### Chat Completion Example

- [chat_completions_example.py](examples/chat_completions_example.py)
- [chat_completions_example_stream.py](examples/chat_completions_example_stream.py)
- [completions_example.py](examples/completions_example.py)
- [completions_example_stream.py](examples/completions_example_stream.py)
- [chat_example.py](examples/chat_example.py)
- [chat_example_stream.py](examples/chat_example_stream.py)

#### Embedding Example

- [embedding_example.py](examples/embedding_example.py)

#### o1 Chat Example

- [o1_chat_example.py](examples/o1_chat_example.py)

#### OpenAI Client Example

- [openai_o3_chat_example.py](examples/o3_chat_example_pyclient.py)

## Folder Structure

The following is an overview of the project's directory structure:

```
$ tree .
.
├── app.py
├── argoproxy
│   ├── chat.py
│   ├── completions.py
│   ├── config.py
│   ├── embed.py
│   ├── extras.py
│   └── utils.py
├── config.yaml
├── examples
│   ├── chat_completions_example.py
│   ├── chat_completions_example_stream.py
│   ├── chat_example.py
│   ├── chat_example_stream.py
│   ├── completions_example.py
│   ├── completions_example_stream.py
│   ├── embedding_example.py
│   ├── o1_chat_example.py
│   ├── o3_chat_example_pyclient.py
│   ├── openai_chat_completions_example_stream.py
│   ├── openai_completions_example_stream.py
│   └── results_compare
│       ├── argo_chunk
│       ├── chat_completions
│       │   ├── my_chunk
│       │   ├── openai_chunk
│       │   └── siliconflow_chunk
│       ├── completions
│       │   ├── my_chunk
│       │   ├── openai_chunk
│       │   └── siliconflow_chunk
│       └── my_chunk
├── LICENSE
├── README.md
├── requirements.txt
├── run_app.sh
└── test
    ├── test2.py
    ├── test2.sh
    ├── test.py
    └── test.sh
```

## Bug Reports and Contributions

This project was developed in my spare time. Bugs and issues may exist. If you encounter any or have suggestions for improvements, please [open an issue](https://github.com/Oaklight/argo-proxy/issues/new) or [submit a pull request](https://github.com/Oaklight/argo-proxy/compare). Your contributions are highly appreciated!

```

In this reordering, I've separated the "Deployment" and "Usage" sections to clarify the process of setting up the application and the ways to interact with it. This should help users who are consuming or deploying the tool identify the relevant information more easily.
```
