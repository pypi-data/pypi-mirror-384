import json
import os
from typing import Any, Dict, Optional, Generator, Union, List

from curl_cffi.requests import Session
from curl_cffi import CurlError

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class OPENAI(Provider):
    """
    A class to interact with the OpenAI API with LitAgent user-agent.
    """
    required_auth = True
    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
        model: str = "gpt-3.5-turbo",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        base_url: str = "https://api.openai.com/v1/chat/completions",
        system_prompt: str = "You are a helpful assistant.",
        browser: str = "chrome"
    ):
        """Initializes the OpenAI API client."""
        self.url = base_url

        # Initialize LitAgent
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.api_key = api_key
        # Use the fingerprint for headers
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "User-Agent": self.fingerprint.get("user_agent", ""),
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # Initialize curl_cffi Session
        self.session = Session()
        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        self.session.proxies = proxies  # Assign proxies directly
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def refresh_identity(self, browser: str = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Update headers with new fingerprint (only relevant ones)
        self.headers.update({
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
        })

        # Update session headers
        self.session.headers.update(self.headers)

        return self.fingerprint

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(f"Optimizer is not one of {self.__available_optimizers}")

        # Payload construction
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }

        def for_stream():
            streaming_text = ""
            try:
                # Use curl_cffi session post with impersonate
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                # Use sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0].get("delta", {}).get("content") if isinstance(chunk, dict) else None,
                    yield_raw_on_error=False
                )

                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        streaming_text += content_chunk
                        resp = dict(text=content_chunk)
                        yield resp if not raw else content_chunk

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {str(e)}") from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {str(e)}") from e
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                # Use curl_cffi session post with impersonate for non-streaming
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                response_text = response.text

                # Use sanitize_stream to parse the non-streaming JSON response
                processed_stream = sanitize_stream(
                    data=response_text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(chunk, dict) else None,
                    yield_raw_on_error=False
                )
                # Extract the single result
                content = next(processed_stream, None)
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}") from e
            except Exception as e:
                err_text = getattr(e, 'response', None) and getattr(e.response, 'text', '')
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {e} - {err_text}") from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        def for_stream_chat():
            gen = self.ask(
                prompt, stream=True, raw=False,
                optimizer=optimizer, conversationally=conversationally
            )
            for response_dict in gen:
                yield self.get_message(response_dict)

        def for_non_stream_chat():
            response_data = self.ask(
                prompt, stream=False, raw=False,
                optimizer=optimizer, conversationally=conversationally
            )
            return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]