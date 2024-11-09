# OProxy

*High-performance, transparent proxy that supports both TCP and UDP protocols.*

A high-performance, transparent proxy that supports both TCP and UDP protocols.

**NOTE:** This proxy has been designed with local API proxy in mind. Specifically, I used it to forward Ollama API requests to the remote Ollama server for applications that try to connect to the local Ollama server on localhost.

## Features

- Transparent TCP proxying
- HTTP/HTTPS proxying without decrypting the traffic
- Optional UDP support
- Detailed logging capabilities
- Configurable through environment variables
- Support for both file and stdout logging
- Data content logging (optional)

## Requirements

- Python 3.7+
- python-dotenv
- socket
- threading

## Installation

1. Clone the repository:

```bash
git clone https://github.com/tcsenpai/oproxy.git

cd oproxy
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```


3. Copy the example environment file:

```bash
cp .env.example .env
```


4. Edit the .env file with your configuration:

```bash
PROXY_PORT=11434
TARGET_HOST=127.0.0.1
TARGET_PORT=80
```


## Usage

Basic TCP proxy:

```bash
python src/main.py
```

Enable logging to file:

```bash
python src/main.py --log-file=proxy.log
```

Enable data logging with debug level:

```bash
python src/main.py --log-file proxy.log --log-data --log-level DEBUG
```

Enable UDP support:

```bash
python src/main.py --enable-udp
```


## Command Line Arguments

- `--log-file`: Path to the log file
- `--log-data`: Enable logging of data content
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--enable-udp`: Enable UDP proxy alongside TCP

## Notes

- TCP proxy runs on the port specified in .env
- UDP proxy (if enabled) runs on PROXY_PORT + 1
- Data logging should be used carefully as it may contain sensitive information
- UDP support is experimental and runs as a daemon thread

## License

MIT License