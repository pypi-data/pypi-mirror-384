# llme, a CLI assitant for OpenAI-compatible chat servers

A simple, single-file command-line chat client compatible with the OpenAI API.

*(or "I just want to quickly test my model hosted with vllm but don't want to spin up openwebui")*

## Features

- **OpenAI API Compatible:** Works with any self-hosted LLM platform that supports OpenAI chat completions API.
- **Extremely simple:** Single file, no installation needed.
- **Command-line interface:** Run it from the terminal.
- **Tools included:** Ask it to act on your file system and edit files (yolo).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/privat/llme.git
   cd llme
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

Or use your operating system's package manager to install python requests, termcolor, and rich

## Usage

```bash
./llme.py --base-url "https://api.openai.com/v1"
```
