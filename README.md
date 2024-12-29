# Argo Proxy Project

This project is a proxy application that forwards requests to an ARGO API and optionally converts the responses to be compatible with OpenAI's API format.

## Table of Contents

* [Prerequisites](#prerequisites)
* [Configuration](#configuration)
* [Running the Application](#running-the-application)
  + [Natively](#natively)
  + [Using Docker](#using-docker)
* [Folder Structure](#folder-structure)
* [Endpoints](#endpoints)
* [Examples](#examples)

## Prerequisites

* Python 3.8 or higher
* Docker (optional, for Docker usage)

## Configuration

The application is configured using a `config.yaml` file. This file contains settings such as the ARGO API URLs, port number, and logging behavior. Below is a breakdown of the configuration options:

### Configuration Options

* **`port`**: The port number on which the application will listen. Default is `44497`.
* **`argo_url`**: The URL of the ARGO API for chat and completions. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"`.
* **`argo_embedding_url`**: The URL of the ARGO API for embeddings. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"`.
* **`user`**: The user name to be used in the requests. Default is `"cels"`.
* **`verbose`**: A boolean flag to control whether to print input and output for debugging. Default is `true`.
* **`num_workers`**: The number of worker processes for Gunicorn. Default is `5`.
* **`timeout`**: The timeout for requests in seconds. Default is `600`.

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

### Natively

1. **Install Dependencies**:
   Ensure you have Python 3.8 or higher installed. Install the required packages using pip:

   

```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Use the provided `run_app.sh` script to start the application:

   

```bash
   ./run_app.sh
   ```

### Using Docker

1. **Build the Docker Image**:
   Ensure you have Docker installed. Build the Docker image using the provided Dockerfile:

   

```bash
   docker build -t argo-proxy .
   ```

2. **Run the Docker Container**:
   Use the provided `run_app.sh` script with the `docker` argument to start the container:

   

```bash
   ./run_app.sh docker
   ```

## Folder Structure

```
$ tree .
.
├── app.py
├── argoproxy
│   ├── chat.py
│   ├── completions.py
│   ├── embed.py
│   ├── extras.py
│   └── utils.py
├── compose.yaml
├── config.yaml
├── Dockerfile
├── Dockerfile.txt
├── README.md
├── requirements.txt
├── run_app.sh
└── test
    ├── chat_example.py
    ├── embedding_example.py
    └── o1-example.py

2 directories, 16 files
```

## Endpoints

The application provides the following endpoints:

* **`/v1/chat`**: Directly proxies requests to the ARGO API.
* **`/v1/chat/completions`**: Proxies requests to the ARGO API and converts the response to OpenAI-compatible format.
* **`/v1/completions`**: Proxies requests to the ARGO API and converts the response to OpenAI-compatible format (legacy).
* **`/v1/embed`**: Proxies requests to the ARGO Embedding API.
* **`/v1/models`**: Returns a list of available models in OpenAI-compatible format.
* **`/v1/status`**: Returns a simple "hello" response from GPT-4o.

## Examples

### Chat Example

For an example of how to use the `/v1/chat/completions` endpoint, see the [ `chat_example.py` ](test/chat_example.py) file.

### Embedding Example

For an example of how to use the `/v1/embed` endpoint, see the [ `embedding_example.py` ](test/embedding_example.py) file.

### O1 Example

For an example of how to use the `/v1/chat` endpoint with the `argo:gpt-o1-preview` model, see the [ `o1-example.py` ](test/o1-example.py) file.

---

### **Changes Made**

1. Added the **Configuration** section with a detailed explanation of the `config.yaml` file and its options.
2. Included an example `config.yaml` file for reference.
3. Ensured the **Configuration** section is properly linked in the Table of Contents.
