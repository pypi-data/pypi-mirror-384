#!/usr/bin/env python3

# Copyright (C) 2025 Jean Privat, based from the work of Dory
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import re
import json
import argparse
import requests
import base64
import mimetypes
from termcolor import colored, cprint
import itertools
import threading
import time
import tomllib
from sseclient import SSEClient
import logging
import subprocess
import magic

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class LLME:
    """The God class of the application."""

    def __init__(self, base_url, model, api_key, system_prompt, yolo, prompts):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.yolo = yolo
        self.prompts = prompts
        self.messages = [] # the sequence of messages with the LLM
        self.files = [] # the list of files to send to the LLM for the next prompt

    def get_model_name(self):
        response = requests.get(f"{self.base_url}/models")
        response.raise_for_status()
        models = response.json()
        ids = [m["id"] for m in models["data"]]
        logger.info(f"Available models from {self.base_url}: {', '.join(ids)}")

        if not self.model:
            self.model = models["data"][0]["id"]
            return

        for m in models["data"]:
            if m["id"] == self.model:
                return

        raise ValueError(f"Error: Model '{self.model}' not found. Available: {', '.join(ids)}")


    def run_tool(self, tool, stdin):
        if self.yolo:
            print(colored(f"YOLO RUN {tool}", "red", attrs=["bold"]))
        else:
            x = input(colored(f"RUN {tool} [Yn]? ", "red", attrs=["bold"])).strip()
            if x not in ['', 'y', 'Y']:
                return None

        proc = subprocess.Popen(
                [tool],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # line-buffered
                )

        # send data to stdin
        # FIXME: avoid deadlock...
        # It's weird there isn't a lib or something to do this properly...
        proc.stdin.write(stdin)
        proc.stdin.close()

        content = ''
        with AnimationManager() as am:
            while line := proc.stdout.read():
                am.stop()
                print(line,end='',flush=True)
                content += line
        proc.wait()
        if not content.endswith('\n'):
            print()

        if proc.returncode != 0:
            print(colored(f"EXIT {proc.returncode}", "red", attrs=["bold"]))

        content = f"```result {tool} exitcode={proc.returncode}\n{content}\n```\n"
        return {"role": "system", "content": content}

    def next_prompt(self):
        if len(self.prompts) > 0:
            user_input = self.prompts.pop(0)
            if os.path.exists(user_input):
                self.files.append(Asset(user_input))
                return None
            if sys.stdin.isatty():
                print(colored(f"{len(self.messages)}> ", "green", attrs=["bold"]), user_input)
        elif sys.stdin.isatty():
            user_input = input(colored(f"{len(self.messages)}> ", "green", attrs=["bold"]))
        else:
            user_input = input()
        if not user_input.endswith('\n'):
            print()

        if user_input == '':
            return None

        if len(self.files) > 0:
            content = [{"type": "text", "text": user_input}]
            for asset in self.files:
                content.append(asset.content())
            self.files = []
            res = {"role": "user", "content": content}
            return res
        else:
            return {"role": "user", "content": user_input}
        return None

    def chat_completion(self):
        with AnimationManager():
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model,
                      "messages": self.messages,
                      "stream": True},
                stream=True
            )
            response.raise_for_status()

        full_content = ''
        cb = None
        for event in SSEClient(response).events():
            if event.data == "[DONE]":
                break
            data = json.loads(event.data)
            choice0 = data['choices'][0]
            if choice0['finish_reason'] == 'stop':
                break
            content = choice0['delta']['content']
            if content is None:
                continue
            full_content += content
            print(content, end='', flush=True)
            cb = re.search(
                r"```run ([\w+-]*)\n(.*?)```", full_content, re.DOTALL)
            if cb:
                break
        if not full_content.endswith('\n'):
            print()
        response.close()
        self.messages.append({"role": "agent", "content": full_content})
        logger.debug(f"Agent response: {self.messages[-1]}")
        if cb:
            r = self.run_tool(cb[1], cb[2])
            if r:
                self.messages.append(r)
                logger.debug(f"Tool result: {self.messages[-1]}")
                return r
        return None

    def start(self):
        self.get_model_name()
        logger.info(f"Use model {self.model} from {self.base_url}")

        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})
            logger.debug(f"System prompt: {self.messages[-1]}")

        if not sys.stdin.isatty():
            if len(self.prompts) > 0:
                # There is prompts, so use stdin as data for the first prompt
                self.prompts.insert(0, "/dev/stdin")
            else:
                # No prompts, so use stdin as prompt
                self.prompts = [sys.stdin.read()]

        while True:
            try:
                prompt = self.next_prompt()
                if prompt:
                    self.messages.append(prompt)
                    logger.debug(f"User prompt: {self.messages[-1]}")
                    while self.chat_completion():
                        pass
            except requests.exceptions.RequestException as e:
                logger.warning(e.response.content)
                raise e
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Use ^D to exit.")
                continue
            except EOFError:
                break


class AnimationManager:
    """A simple context manager for a spinner animation."""
    def animate(self):
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if self.stop_event.is_set():
                break
            sys.stdout.write(f'\r{colored(c, "green", attrs=["bold"])} ')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r')
        sys.stdout.flush()

    def stop(self):
        if sys.stdin.isatty() and not self.stop_event.is_set():
            self.stop_event.set()
            self.animation_thread.join()

    def __enter__(self):
        if sys.stdin.isatty():
            self.stop_event = threading.Event()
            self.animation_thread = threading.Thread(target=self.animate)
            self.animation_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

class Asset:
    "A loaded file"
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.raw_content = f.read()
        self.mime_type = magic.from_buffer(self.raw_content, mime=True)
        logger.info(f"File {path} is {self.mime_type}")

    def content(self):
        if self.mime_type.startswith("text/"):
            data = self.raw_content.decode()
            return {"type": "file", "file": {"filename": self.path, "file_data": data}}
        elif self.mime_type.startswith("image/"):
            data = base64.b64encode(self.raw_content).decode()
            url = f"data:{self.mime_type};base64,{data}"
            return {"type": "image_url", "image_url": {"url": url}}
        else:
            data = base64.b64encode(self.raw_content).decode()
            return {"type": "file", "file": {"filename": self.path, "file_data": data}}

def apply_config(args, config):
    """
    Use default config value is absent from args.
    The method is a little ugly but it works...
    """
    variables = vars(args)
    for k in variables:
        if variables[k] is None and k in config:
            setattr(args, k, config[k])

def main():
    config_path = os.path.join(os.environ.get( "HOME"), ".config", "llme", "config.toml")
    parser = argparse.ArgumentParser(description="OpenAI-compatible chat CLI")
    parser.add_argument("-u", "--base-url", help="API base URL")
    parser.add_argument("-m", "--model", help="Model name")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument( "-s", "--system", dest="system_prompt", help="System prompt")
    parser.add_argument("-c", "--config", help="Custom configuration file")
    parser.add_argument("-v", "--verbose", default=0, action="count", help="Increase verbosity level (can be used multiple times)")
    parser.add_argument("-Y", "--yolo", action="store_true", help="UNSAFE: Do not ask for confirmation before running tools")
    parser.add_argument("prompts", nargs="*", help="Sequence of prompts")

    args = parser.parse_args()

    logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logger.setLevel(logging_levels[min(args.verbose, len(logging_levels)-1)])
    del(args.verbose)

    if args.config or os.path.exists(config_path):
        with open(args.config or config_path, "rb") as f:
            config = tomllib.load(f)
        apply_config(args, config)
    del (args.config)

    if args.base_url is None:
        print("Error: --base-url required and not definied the config file.", file=sys.stderr)
        sys.exit(1)

    llme = LLME(**vars(args))
    llme.start()

if __name__ == "__main__":
    main()
