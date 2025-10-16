import json
from typing import Dict, Optional, Tuple, Union

import litellm
from litellm import ModelResponse, completion
from litellm.caching.caching import Cache

from highlighter.agent.capabilities import Capability, StreamEvent

__all__ = ["LLM"]


class LLM(Capability):
    """
    Parameters used by this capability:


    model: str: name of the model to use. Default: "claude-3-haiku-20240307"

    prompt_template: str: The prompt to use the context of the process_frame 'text'
        param will be inserted at {{PLACEHOLDER}}

    prompt_template_path: str: If used the `prompt_template` will be overwirtten
        with the contents of the template file.

    system_prompt_template: str: The system prompt template to use

    system_prompt_template_path: str: If used the `system_prompt_template` will be overwirtten
        with the contents of the template file.

    mock_response: bool: mock responses from llm, Defaut `true`

    num_retries: int: Number of retries. Default: 8

    completion_kwargs": {"temperature": 0.5}
        timeout: float | int | None = None
        temperature: float | None = None
        top_p: float | None = None
        n: int | None = None
        stream: bool | None = None
        stop: Unknown | None = None
        max_tokens: int | None = None
        presence_penalty: float | None = None
        frequency_penalty: float | None = None
        logit_bias: dict[Unknown, Unknown] | None = None
        user: str | None = None
        response_format: dict[Unknown, Unknown] | None = None
        seed: int | None = None
        tools: List[Unknown] | None = None
        tool_choice: str | None = None
        logprobs: bool | None = None
        top_logprobs: int | None = None
        deployment_id: Unknown | None = None
        extra_headers: dict[Unknown, Unknown] | None = None
        functions: List[Unknown] | None = None
        function_call: str | None = None
        base_url: str | None = None
        api_version: str | None = None
        api_key: str | None = None
        model_list: list[Unknown] | None = None
    """

    class InitParameters(Capability.InitParameters):
        cache_system_prompt: bool = False
        completion_kwargs: dict = {}
        mock_response: bool = True
        model: str = "claude-3-haiku-20240307"
        num_retries: int = 8
        prompt_template: Optional[str] = None
        system_prompt_template: Optional[str] = None

    class StreamParameters(InitParameters):
        prompt_template_path: Optional[str] = None
        system_prompt_template_path: Optional[str] = None

    def __init__(self, context):
        super().__init__(context)
        self.prompt_template: str = self.init_parameters.prompt_template
        self.system_prompt_template: Optional[str] = self.init_parameters.system_prompt_template

        litellm.cache = Cache(type="disk")
        litellm.success_callback = [self.log_success_event]
        litellm.failure_callback = [self.log_failure_event]
        litellm._logging._disable_debugging()

    def start_stream(self, stream, stream_id) -> Tuple[StreamEvent, Optional[str]]:
        parameters = self.stream_parameters(stream.stream_id)

        if parameters.prompt_template_path is not None:
            with open(parameters.prompt_template_path, "r") as f:
                self.prompt_template = f.read()
        if not self.prompt_template:
            raise ValueError("Must supply 'prompt_template'")

        if parameters.system_prompt_template_path is not None:
            with open(parameters.system_prompt_template_path, "r") as f:
                self.system_prompt_template = f.read()
        if not self.system_prompt_template:
            raise ValueError("Must supply 'system_prompt_template'")

        if parameters.strategy is None:
            raise ValueError("Agent parameter 'strategy' is not set.")

        elif parameters.strategy in ["select_all", "pass", "completion"]:
            pass

        else:
            raise ValueError("Agent parameter 'strategy' needs valid value.")

        return StreamEvent.OKAY, None

    def process_frame(self, stream, text: str) -> Tuple[StreamEvent, Union[Dict, str]]:
        """

        text: str

        """
        parameters = self.stream_parameters(stream.stream_id)
        if parameters.strategy == "select_all":
            return StreamEvent.OKAY, {"text": "select_all", "input_text": text}
        elif parameters.strategy == "pass":
            return StreamEvent.OKAY, {"text": "pass", "input_text": text}

        if not isinstance(text, str):
            raise TypeError(f"Invalid content type, expected str got type '{type(text)}' with value '{text}'")

        prompt = self.prompt_template.replace("{{PLACEHOLDER}}", text)

        content = ""

        try:
            messages = []
            system = []

            if self.system_prompt_template:
                if parameters.cache_system_prompt:
                    system.append(
                        {
                            "type": "text",
                            "text": self.system_prompt_template,
                            "cache_control": {"type": "ephemeral"},
                        }
                    )
                else:
                    system.append({"type": "text", "text": self.system_prompt_template})

                messages.append({"content": system, "role": "system"})

            messages.append({"content": prompt, "role": "user"})

            if parameters.mock_response:
                mock_content = json.dumps([{"mock_response": "mock_response_value"}] * 3)
                response = ModelResponse(**{"choices": [{"message": {"content": mock_content}}]})
            else:
                response: ModelResponse = completion(
                    model=parameters.model,
                    messages=messages,
                    num_retries=parameters.num_retries,
                    caching=True,
                    **parameters.completion_kwargs,
                )

            content = response["choices"][0]["message"]["content"]
        except Exception as e:
            message = f"Error while calling Litellm.completion, got: {e}"
            self.logger.error(message)
            return StreamEvent.ERROR, {"diagnostic": message}

        return StreamEvent.OKAY, {"text": content, "input_text": text}

    def write_log(self, response_type, kwargs, response_obj, start_time, end_time):
        time_log_msgs = []
        if start_time is not None and end_time is not None:
            time_log_msgs.append(f"time: {timedelta_to_readable(end_time - start_time)}")

        base_log_messages = []

        if "response_cost" in kwargs:
            base_log_messages.append(f'response_cost: {round(kwargs["response_cost"], 6)}')

        if "cache_hit" in kwargs:
            cache_hit_y_n = "y" if kwargs["cache_hit"] else "n"
            base_log_messages.append(f"response_cache: {cache_hit_y_n}")

        identity_log_messages = []
        response_log_messages = []

        content = []

        if response_obj is not None:
            try:
                content = json.loads(response_obj["choices"][0]["message"]["content"])
                content = content if isinstance(content, list) else [content]
            except:
                raise ValueError(f"Couldn't parse response content: '{response_obj}'")

            if "usage" in response_obj:
                usage = response_obj["usage"]

                if "cache_creation_input_tokens" in usage:
                    prompt_cache_input_tokens = usage["cache_creation_input_tokens"]
                    if prompt_cache_input_tokens > 0:
                        response_log_messages.append(
                            f"prompt_cache_input_tokens: {prompt_cache_input_tokens}"
                        )

                if "cache_read_input_tokens" in usage:
                    cache_read_input_tokens = usage["cache_read_input_tokens"]
                    if cache_read_input_tokens > 0:
                        response_log_messages.append(
                            f"prompt_cache_read_input_tokens: {cache_read_input_tokens}"
                        )

        identity_log_messages = [json.dumps(content[0])]

        self.logger.info(
            f"LLM {response_type} "
            + " ".join(
                map(str, identity_log_messages + time_log_msgs + base_log_messages + response_log_messages)
            )
        )

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        self.write_log("success", kwargs, response_obj, start_time, end_time)

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        self.write_log("failure", kwargs, response_obj, start_time, end_time)


def timedelta_to_readable(time_delta):
    days = time_delta.days
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = time_delta.microseconds // 1000  # Convert microseconds to milliseconds

    time_parts = []
    if days > 0:
        time_parts.append(str(days))
    if hours > 0 or days > 0:
        time_parts.append(f"{str(hours)}hr")
    if minutes > 0 or hours > 0 or days > 0:
        time_parts.append(f"{str(minutes)}min")
    if seconds > 0 or minutes > 0 or hours > 0 or days > 0:
        time_parts.append(f"{str(seconds)}s")
    if milliseconds > 0 or len(time_parts) > 0:
        time_parts.append(f"{str(milliseconds)}ms")

    return " ".join(time_parts)
