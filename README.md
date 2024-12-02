# Argo Proxy Project

This project is a proxy application that forwards requests to an ARGO API and optionally converts the responses to be compatible with OpenAI's API format.

## Table of Contents

* [Prerequisites](#prerequisites)
* [Configuration](#configuration)
* [Running the Application](#running-the-application)
  + [Natively](#natively)
  + [Using Docker](#using-docker)
* [Configuration File](#configuration-file)

## Prerequisites

* Python 3.8 or higher
* Docker (optional, for Docker usage)

## Configuration

The application uses a `config.yaml` file to manage its settings. This file includes the following fields:

* `port`: The port number for the application to listen on.
* `argo_url`: The URL of the ARGO API.
* `user`: The user name to be used in the requests.
* `verbose`: A boolean flag to control whether to print input and output (default: `false`).
* `num_workers`: The number of worker processes for Gunicorn (default: `4`).

### Example `config.yaml`

```yaml
port: 6000
argo_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
user: "cels"
verbose: false
num_workers: 4
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

## Configuration File

The `config.yaml` file allows you to customize the application's behavior. Here are the available settings:

* **port**: The port number on which the application will listen. Default is `6000`.
* **argo_url**: The URL of the ARGO API. Default is `"https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"`.
* **user**: The user name to be used in the requests. Default is `"cels"`.
* **verbose**: A boolean flag to control whether to print input and output. Default is `false`.
* **num_workers**: The number of worker processes for Gunicorn. Default is `4`.

### Example `config.yaml`

```yaml
port: 6000
argo_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
user: "cels"
verbose: false
num_workers: 4
