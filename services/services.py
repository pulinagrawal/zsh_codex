import os
import sys
from abc import ABC, abstractmethod
from configparser import ConfigParser

CONFIG_DIR = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
CONFIG_PATH = os.path.join(CONFIG_DIR, "zsh_codex.ini")


class BaseClient(ABC):
    """Base class for all clients"""

    api_type: str = None
    system_prompt = "You are a zsh shell expert, please help me complete the following command, you should only output the completed command, do not include any explanation, comments or any other text that is not part of the command. Do not put completed command in a code block."

    @abstractmethod
    def get_completion(self, full_command: str) -> str:
        pass


class OpenAIClient(BaseClient):
    """
    config keys:
        - api_type="openai"
        - api_key (required)
        - base_url (optional): defaults to "https://api.openai.com/v1".
        - organization (optional): defaults to None
        - model (optional): defaults to "gpt-4o-mini"
        - temperature (optional): defaults to 1.0.
    """

    api_type = "openai"
    default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")

    def __init__(self, config: dict):
        try:
            from openai import OpenAI
        except ImportError:
            print(
                "OpenAI library is not installed. Please install it using 'pip install openai'"
            )
            sys.exit(1)

        self.config = config
        self.config["model"] = self.config.get("model", self.default_model)
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config.get("base_url", "https://api.openai.com/v1"),
            organization=self.config.get("organization"),
        )

    def get_completion(self, full_command: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "# list all files with all attributes in current folder"},
                {"role": "assistant", "content": "ls -alhi"},
                {"role": "user", "content": "# go one directory up"},
                {"role": "assistant", "content": "cd .."},
                {"role": "user", "content": full_command},
            ],

            temperature=float(self.config.get("temperature", 0.0)),
        )
        return response.choices[0].message.content


class GoogleGenAIClient(BaseClient):
    """
    config keys:
        - api_type="gemeni"
        - api_key (required)
        - model (optional): defaults to "gemini-1.5-pro-latest"
    """

    api_type = "gemeni"
    default_model = os.getenv("GOOGLE_GENAI_DEFAULT_MODEL", "gemini-1.5-pro-latest")

    def __init__(self, config: dict):
        try:
            import google.generativeai as genai
        except ImportError:
            print(
                "Google Generative AI library is not installed. Please install it using 'pip install google-generativeai'"
            )
            sys.exit(1)

        self.config = config
        genai.configure(api_key=self.config["api_key"])
        self.config["model"] = config.get("model", self.default_model)
        self.model = genai.GenerativeModel(self.config["model"])

    def get_completion(self, full_command: str) -> str:
        chat = self.model.start_chat(history=[
            {
                "role": "user",
                "parts": [f"{self.system_prompt}\n\n# list all files with all attributes in current folder"]
            },
            {
                "role": "model", 
                "parts": ["ls -alhi"]
            },
            {
                "role": "user",
                "parts": ["# go one directory up"]
            },
            {
                "role": "model",
                "parts": ["cd .."]
            }
        ])
        response = chat.send_message(full_command)
        return response.text


class GroqClient(BaseClient):
    """
    config keys:
        - api_type="groq"
        - api_key (required)
        - model (optional): defaults to "llama-3.2-11b-text-preview"
        - temperature (optional): defaults to 1.0.
    """
    
    api_type = "groq"
    default_model = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.2-11b-text-preview")
    
    def __init__(self, config: dict):
        try:
            from groq import Groq
        except ImportError:
            print(
                "Groq library is not installed. Please install it using 'pip install groq'"
            )
            sys.exit(1)

        self.config = config
        self.config["model"] = self.config.get("model", self.default_model)
        self.client = Groq(
            api_key=self.config["api_key"],
        )
    
    def get_completion(self, full_command: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "# list all files with all attributes in current folder"},
                {"role": "assistant", "content": "ls -alhi"},
                {"role": "user", "content": "# go one directory up"},
                {"role": "assistant", "content": "cd .."},
                {"role": "user", "content": full_command},
            ],
            temperature=float(self.config.get("temperature", 0.0)),
        )
        return response.choices[0].message.content


class MistralClient(BaseClient):
    """
    config keys:
        - api_type="mistral"
        - api_key (required)
        - model (optional): defaults to "codestral-latest"
        - temperature (optional): defaults to 1.0.
    """
    
    api_type = "mistral"
    default_model = os.getenv("MISTRAL_DEFAULT_MODEL", "codestral-latest")
    
    def __init__(self, config: dict):
        try:
            from mistralai import Mistral
        except ImportError:
            print(
                "Mistral library is not installed. Please install it using 'pip install mistralai'"
            )
            sys.exit(1)
        
        self.config = config
        self.config["model"] = self.config.get("model", self.default_model)
        self.client = Mistral(
            api_key=self.config["api_key"],
        )
        
    def get_completion(self, full_command: str) -> str:
        response = self.client.chat.complete(
            model=self.config["model"],
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "# list all files with all attributes in current folder"},
                {"role": "assistant", "content": "ls -alhi"},
                {"role": "user", "content": "# go one directory up"},
                {"role": "assistant", "content": "cd .."},
                {"role": "user", "content": full_command},
            ],
            temperature=float(self.config.get("temperature", 0.0)),
        )
        return response.choices[0].message.content

class AmazonBedrock(BaseClient):
    """
    config keys:
        - api_type="bedrock"
        - aws_region (optional): defaults to environment variable AWS_REGION
        - aws_access_key_id (optional): defaults to environment variable AWS_ACCESS_KEY_ID
        - aws_secret_access_key (optional): defaults to environment variable AWS_SECRET_ACCESS_KEY
        - aws_session_token (optional): defaults to environment variable AWS_SESSION_TOKEN
        - model (optional): defaults to "anthropic.claude-3-5-sonnet-20240620-v1:0" or environment variable BEDROCK_DEFAULT_MODEL
        - temperature (optional): defaults to 1.0.
    """

    api_type = "bedrock"
    default_model = os.getenv("BEDROCK_DEFAULT_MODEL", "anthropic.claude-3-5-sonnet-20240620-v1:0")

    def __init__(self, config: dict):
        try:
            import boto3
        except ImportError:
            print(
                "Boto3 library is not installed. Please install it using 'pip install boto3'"
            )
            sys.exit(1)

        self.config = config
        self.config["model"] = self.config.get("model", self.default_model)

        session_kwargs = {}
        if "aws_region" in config:
            session_kwargs["region_name"] = config["aws_region"]
        if "aws_access_key_id" in config:
            session_kwargs["aws_access_key_id"] = config["aws_access_key_id"]
        if "aws_secret_access_key" in config:
            session_kwargs["aws_secret_access_key"] = config["aws_secret_access_key"]
        if "aws_session_token" in config:
            session_kwargs["aws_session_token"] = config["aws_session_token"]

        self.client = boto3.client("bedrock-runtime", **session_kwargs)

    def get_completion(self, full_command: str) -> str:
        import json

        messages = [
            {"role": "user", "content": "# list all files with all attributes in current folder"},
            {"role": "assistant", "content": "ls -alhi"},
            {"role": "user", "content": "# go one directory up"},
            {"role": "assistant", "content": "cd .."},
            {"role": "user", "content": full_command}
        ]

        # Format request body based on model type
        if "claude" in self.config["model"].lower():
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": self.system_prompt,
                "messages": messages,
                "temperature": float(self.config.get("temperature", 0.0))
            }
        else:
            raise ValueError(f"Unsupported model: {self.config['model']}")

        response = self.client.invoke_model(
            modelId=self.config["model"],
            body=json.dumps(body)
        )

        response_body = json.loads(response['body'].read())
        return response_body["content"][0]["text"]


class OllamaClient(BaseClient):
    """
    config keys:
        - api_type="ollama"
        - base_url (optional): defaults to "http://localhost:11434"
        - model (optional): defaults to "llama3.2" or environment variable OLLAMA_DEFAULT_MODEL
        - temperature (optional): defaults to 1.0.
    """

    api_type = "ollama"
    default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2")

    def __init__(self, config: dict):
        try:
            import ollama
        except ImportError:
            print(
                "Ollama library is not installed. Please install it using 'pip install ollama'"
            )
            sys.exit(1)

        self.config = config
        self.config["model"] = self.config.get("model", self.default_model)
        
        # Create ollama client with custom host if specified
        if "base_url" in self.config:
            self.client = ollama.Client(host=self.config["base_url"])
        else:
            self.client = ollama.Client()

    def get_completion(self, full_command: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": "# list all files with all attributes in current folder"},
            {"role": "assistant", "content": "ls -alhi"},
            {"role": "user", "content": "# go one directory up"},
            {"role": "assistant", "content": "cd .."},
            {"role": "user", "content": full_command}
        ]
        
        response = self.client.chat(
            model=self.config["model"],
            messages=messages,
            options={
                "temperature": float(self.config.get("temperature", 0.0))
            },
            think=True
        )
        
        return response["message"]["content"]


class ClientFactory:
    api_types = [OpenAIClient.api_type, GoogleGenAIClient.api_type, GroqClient.api_type, MistralClient.api_type, AmazonBedrock.api_type, OllamaClient.api_type]

    @classmethod
    def create(cls):
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        service = config_parser["service"]["service"]
        try:
            config = {k: v for k, v in config_parser[service].items()}
        except KeyError:
            raise KeyError(f"Config for service {service} is not defined")

        api_type = config["api_type"]
        match api_type:
            case OpenAIClient.api_type:
                return OpenAIClient(config)
            case GoogleGenAIClient.api_type:
                return GoogleGenAIClient(config)
            case GroqClient.api_type:
                return GroqClient(config)
            case MistralClient.api_type:
                return MistralClient(config)
            case AmazonBedrock.api_type:
                return AmazonBedrock(config)
            case OllamaClient.api_type:
                return OllamaClient(config)
            case _:
                raise KeyError(
                    f"Specified API type {api_type} is not one of the supported services {cls.api_types}"
                )
