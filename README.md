# argo-openai-proxy

This project is a proxy application that forwards requests to an ARGO API and optionally converts the responses to be compatible with OpenAI's API format. It can be used in conjunction with [autossh-tunnel-dockerized](https://github.com/Oaklight/autossh-tunnel-dockerized) or other secure connection tools.

## NOTICE OF USAGE

The machine or server making API calls to Argo must be connected to the Argonne internal network or through a VPN on an Argonne-managed computer if you are working off-site. Your instance of the argo proxy should always be on-premise at an Argonne machine. The software is provided "as is," without any warranties. By using this software, you accept that the authors, contributors, and affiliated organizations will not be liable for any damages or issues arising from its use. You are solely responsible for ensuring the software meets your requirements.

- [Notice of Usage](#notice-of-usage)
- [Deployment](#deployment)
  - [Prerequisites](#prerequisites)
  - [Configuration File](#configuration-file)
  - [Running the Application](#running-the-application)
  - [First-Time Setup](#first-time-setup)
  - [Configuration Options Reference](#configuration-options-reference)
- [Usage](#usage)
  - [Endpoints](#endpoints)
    - [OpenAI Compatible](#openai-compatible)
    - [Not OpenAI Compatible](#not-openai-compatible)
    - [Timeout Override](#timeout-override)
  - [Models](#models)
    - [Chat Models](#chat-models)
    - [Embedding Models](#embedding-models)
  - [Examples](#examples)
    - [Chat Completion Example](#chat-completion-example)
    - [Embedding Example](#embedding-example)
    - [o1 Chat Example](#o1-chat-example)
    - [OpenAI Client Example](#openai-client-example)
- [Folder Structure](#folder-structure)
- [Bug Reports and Contributions](#bug-reports-and-contributions)

## Deployment

### Prerequisites

- **Python 3.10+** is required \
  recommend to use conda/mamba or pipx etc to manage exclusive environment \
  **Conda/Mamba** Download and install from: <https://conda-forge.org/download/>

- Install dependencies:

  ```bash
  pip install .
  ```

### Configuration File

If you don't want to bother manually configure it, the [First-Time Setup](#first-time-setup) will automatically create it for you.

The application uses `config.yaml` for configuration. Here's an example:

```yaml
port: 44497
argo_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
argo_stream_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
argo_embedding_url: "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
user: "your_username" # set during first-time setup
verbose: true # can be changed during setup
num_workers: 5
timeout: 600 # in seconds
```

### Running the Application

To start the application:

```bash
./run_app.sh [config_path]
```

- Without arguments: uses `config.yaml` in current directory
- With path: uses specified config file

  ```bash
  ./run_app.sh /path/to/config.yaml
  ```

### First-Time Setup

When running without an existing config file:

1. The script offers to create `config.yaml` from `config.sample.yaml`
2. Automatically selects a random available port (can be overridden)
3. Prompts for:
   - Your username (sets `user` field)
   - Verbose mode preference (sets `verbose` field)
4. Validates connectivity to configured URLs
5. Shows the generated config in a formatted display for review before proceeding

Example session:

```bash
$ ./run_app.sh
config.yaml file not found.
Would you like to create it from config.sample.yaml? [y/N] y
Enter your username: your_username
Enable verbose mode? [Y/n] y
Created config.yaml with your settings:
--------------------------------------
port: 44497
argo_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
argo_stream_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
argo_embedding_url: "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
user: "your_username"
verbose: true
num_workers: 5
timeout: 600
--------------------------------------
Review the config above. Press enter to continue or Ctrl+C to abort.
```

### Configuration Options Reference

| Option               | Description                                                  | Default            |
| -------------------- | ------------------------------------------------------------ | ------------------ |
| `port`               | Application port (random available port selected by default) | randomly assigned  |
| `argo_url`           | ARGO chat API URL                                            | Dev URL (for now)  |
| `argo_stream_url`    | ARGO stream API URL                                          | Dev URL (for now)  |
| `argo_embedding_url` | ARGO embedding API URL                                       | Prod URL           |
| `user`               | Your username                                                | (Set during setup) |
| `verbose`            | Debug logging                                                | `true`             |
| `num_workers`        | Worker processes                                             | `5`                |
| `timeout`            | Request timeout (seconds)                                    | `600`              |

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

| Original ARGO Model Name | Argo Proxy Name                          |
| ------------------------ | ---------------------------------------- |
| `gpt35`                  | `argo:gpt-3.5-turbo`                     |
| `gpt35large`             | `argo:gpt-3.5-turbo-16k`                 |
| `gpt4`                   | `argo:gpt-4`                             |
| `gpt4large`              | `argo:gpt-4-32k`                         |
| `gpt4turbo`              | `argo:gpt-4-turbo-preview`               |
| `gpt4o`                  | `argo:gpt-4o`                            |
| `gpt4olatest`            | `argo:gpt-4o-latest`                     |
| `gpto1preview`           | `argo:gpt-o1-preview`, `argo:o1-preview` |
| `gpto1mini`              | `argo:gpt-o1-mini` , `argo:o1-mini`      |
| `gpto3mini`              | `argo:gpt-o3-mini` , `argo:o3-mini`      |
| `gpto1`                  | `argo:gpt-o1` , `argo:o1`                |

#### Embedding Models

| Original ARGO Model Name | Argo Proxy Name               |
| ------------------------ | ----------------------------- |
| `ada002`                 | `argo:text-embedding-ada-002` |
| `v3small`                | `argo:text-embedding-3-small` |
| `v3large`                | `argo:text-embedding-3-large` |

### Examples

#### Chat Completion Example

For an example of how to use the `/v1/chat/completions`, /v1/completions`, /v1/chat` endpoint, see the followings:

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
$ tree -I "__pycache__|*.egg-info|dev_scripts|config.yaml"
.
├── app.py
├── argoproxy
│   ├── chat.py
│   ├── completions.py
│   ├── config.py
│   ├── constants.py
│   ├── embed.py
│   ├── extras.py
│   └── utils.py
├── config.sample.yaml
├── examples
│   ├── chat_completions_example.py
│   ├── chat_completions_example_stream.py
│   ├── chat_example.py
│   ├── chat_example_stream.py
│   ├── completions_example.py
│   ├── completions_example_stream.py
│   ├── embedding_example.py
│   ├── o1_chat_example.py
│   └── o3_chat_example_pyclient.py
├── LICENSE
├── pyproject.toml
├── README.md
├── run_app.sh
└── timeout_examples.md

3 directories, 23 files
```

## Bug Reports and Contributions

This project was developed in my spare time. Bugs and issues may exist. If you encounter any or have suggestions for improvements, please [open an issue](https://github.com/Oaklight/argo-proxy/issues/new) or [submit a pull request](https://github.com/Oaklight/argo-proxy/compare). Your contributions are highly appreciated!
