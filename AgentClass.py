"""LLM agent adapters used by the PhysMent experiment runner."""

import os
from dotenv import load_dotenv
import config

load_dotenv()


class OpenAIAgent:
    """Adapter for OpenAI chat-completion models."""
    def __init__(
        self,
        model: str = config.OPENAI_MODEL,
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
        """Initialize the instance."""
        import openai
        import backoff
        from openai.types.chat import (
            ChatCompletionSystemMessageParam,
            ChatCompletionUserMessageParam,
            ChatCompletionAssistantMessageParam,
        )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self._openai = openai
        self._backoff = backoff
        self.system_prompt = system_prompt
        self.model = model
        self.context: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
        ] = [{"role": "system", "content": system_prompt}]

    def interact(self, user_input):
        """Send user input to the model and return its response."""
        openai = self._openai

        @self._backoff.on_exception(self._backoff.expo, openai.RateLimitError)
        def _call():
            """Call the model API with retry handling."""
            self.context.append({"role": "user", "content": user_input})
            response = openai.chat.completions.create(
                model=self.model,
                messages=self.context,
                max_completion_tokens=config.max_tokens,
            )
            ai_message = response.choices[0].message.content
            self.context.append({"role": "assistant", "content": ai_message})
            return ai_message

        return _call()


class OpenRouterAgent:
    """Adapter for OpenRouter-hosted chat-completion models."""
    def __init__(
        self,
        model: str = config.OPENROUTER_MODEL,
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
        """Initialize the instance."""
        import openai
        import backoff
        from openai.types.chat import (
            ChatCompletionSystemMessageParam,
            ChatCompletionUserMessageParam,
            ChatCompletionAssistantMessageParam,
        )

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self._client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._openai = openai
        self._backoff = backoff
        self.system_prompt = system_prompt
        self.model = model
        self.context: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
        ] = [{"role": "system", "content": system_prompt}]

    def interact(self, user_input):
        """Send user input to the model and return its response."""
        openai = self._openai

        @self._backoff.on_exception(self._backoff.expo, openai.RateLimitError)
        def _call():
            """Call the model API with retry handling."""
            self.context.append({"role": "user", "content": user_input})
            response = self._client.chat.completions.create(
                model=self.model,
                messages=self.context,
                max_tokens=config.max_tokens,
                extra_body={"provider": {"data_collection": "deny"}},
            )
            ai_message = response.choices[0].message.content
            self.context.append({"role": "assistant", "content": ai_message})
            return ai_message

        return _call()


class AnthropicAgent:
    """Adapter for Anthropic Claude message models."""
    def __init__(
        self,
        model: str = config.ANTHROPIC_MODEL,
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
        """Initialize the instance."""
        import anthropic

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.context = []

    def interact(self, user_input):
        """Send user input to the model and return its response."""
        msg = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=self.context + [{"role": "user", "content": user_input}],
            max_tokens=config.max_tokens,
        )
        ai_message = msg.content[0].text  # type: ignore
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": ai_message})
        return ai_message


class GeminiAgent:
    """Adapter for Google Gemini models."""
    def __init__(
        self,
        model_name: str = config.GEMINI_MODEL,
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
        """Initialize the instance."""
        from google.generativeai.generative_models import GenerativeModel
        from google.generativeai.client import configure

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        configure(api_key=self.api_key)
        self.model = GenerativeModel(model_name=model_name)
        self.system_prompt = system_prompt
        self.context = []

    def interact(self, user_input):
        """Send user input to the model and return its response."""
        prompt = "System: " + self.system_prompt + "\n"
        for msg in self.context:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        prompt += f"User: {user_input}\nAssistant:"
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": config.max_tokens,
            },
        )
        ai_message = response.text
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": ai_message})
        return ai_message


class BaseTogetherAgent:
    """Shared adapter for Together-hosted chat models."""
    def __init__(self, api_key=None, model_name=None, system_prompt=None):
        """Initialize the instance."""
        from together import Together

        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        self.client = Together(api_key=self.api_key)
        self.model_name = model_name
        self.system_prompt = (
            system_prompt
            or """You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function."""
        )
        self.context = []

    def interact(self, user_input):
        # Compose messages for Together.ai chat
        """Send user input to the model and return its response."""
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + self.context
            + [{"role": "user", "content": user_input}]
        )

        # Call Together API chat completion (no streaming here)
        response_stream = self.client.chat.completions.create(
            model=self.model_name,  # type: ignore
            messages=messages,
            stream=False,  # Disable streaming for this use-case
            max_tokens=config.max_tokens,
        )

        ai_message = response_stream.choices[0].message.content  # type: ignore

        # Update context
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": ai_message})

        return ai_message


# Specific agents with their respective model names


class LlamaAgent(BaseTogetherAgent):
    """Together adapter for the configured Llama model."""
    def __init__(self, api_key=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name="meta-llama/Llama-4-Scout-17B-16E-Instruct",
            system_prompt=system_prompt,
        )


class GemmaAgent(BaseTogetherAgent):
    """Together adapter for the configured Gemma model."""
    def __init__(self, api_key=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name="google/gemma-2-27b-it",
            system_prompt=system_prompt,
        )


class DeepSeekAgent(BaseTogetherAgent):
    """Together adapter for DeepSeek R1 with thinking-output handling."""
    def __init__(self, api_key=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name=config.DEEPSEEK_MODEL,
            system_prompt=system_prompt,
        )

    def interact(self, user_input, _max_retries=3):
        """Send user input to the model and return its response."""
        import re

        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + self.context
            + [{"role": "user", "content": user_input}]
        )

        for attempt in range(_max_retries):
            print(
                f"[DeepSeek] API call attempt {attempt + 1}/{_max_retries} (input messages: {len(messages)})..."
            )
            response_stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False,
                max_tokens=32768,
                timeout=config.timeout_limit,  # 10 min — DeepSeek R1 thinking can take a long time
            )
            raw = response_stream.choices[0].message.content or ""
            finish_reason = response_stream.choices[0].finish_reason
            print(
                f"[DeepSeek] Response received. finish_reason={finish_reason!r}, len={len(raw)} chars, has_think_close={'</think>' in raw}"
            )

            # Check if thinking block completed
            think_closed = "</think>" in raw

            if think_closed or finish_reason != "length":
                # Extract only the content after </think>
                after_think = re.split(r"</think>", raw, maxsplit=1)[-1].strip()
                print(
                    f"[DeepSeek] Returning {len(after_think)} chars of post-think content."
                )

                # Strip <think>...</think> for context storage to prevent token bloat
                context_message = re.sub(
                    r"<think>.*?</think>", "", raw, flags=re.DOTALL
                ).strip()
                self.context.append({"role": "user", "content": user_input})
                self.context.append({"role": "assistant", "content": context_message})

                return after_think if after_think else raw

            # Thinking was cut off — nudge the model to output the tool call directly
            print(
                f"[DeepSeek] Thinking was cut off (finish_reason={finish_reason!r}). Nudging for JSON output..."
            )
            messages = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": "Your thinking was cut off. Please output your tool call JSON now, skipping further reasoning.",
                },
            ]

        # Exhausted retries — return whatever we have after </think>, or the raw text
        print(f"[DeepSeek] Exhausted retries. Returning best available output.")
        after_think = re.split(r"</think>", raw, maxsplit=1)[-1].strip()
        context_message = re.sub(
            r"<think>.*?</think>", "", raw, flags=re.DOTALL
        ).strip()
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": context_message})
        return after_think if after_think else raw


class Llama3370BAgent(BaseTogetherAgent):
    """Together adapter for Llama 3.3 70B."""
    def __init__(self, api_key=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            system_prompt=system_prompt,
        )


class QwenAgent(BaseTogetherAgent):
    """Together adapter for the configured Qwen model."""
    def __init__(self, api_key=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name=config.QWEN_MODEL,
            system_prompt=system_prompt,
        )


class MixtralAgent(BaseTogetherAgent):
    """Together adapter for the configured Mixtral model."""
    def __init__(self, api_key=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
            system_prompt=system_prompt,
        )


class KimiAgent(BaseTogetherAgent):
    """Together adapter for the configured Kimi model."""
    def __init__(self, api_key=None, model_name=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name=config.KIMI_MODEL,
            system_prompt=system_prompt,
        )


class GLMAgent(BaseTogetherAgent):
    """Together adapter for the configured GLM model."""
    def __init__(self, api_key=None, model_name=None, system_prompt=None):
        """Initialize the instance."""
        super().__init__(
            api_key=api_key,
            model_name=config.GLM_MODEL,
            system_prompt=system_prompt,
        )
