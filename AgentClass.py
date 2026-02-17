import os
from dotenv import load_dotenv

load_dotenv()


class OpenAIAgent:
    def __init__(
        self,
        model: str,
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
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
        openai = self._openai

        @self._backoff.on_exception(self._backoff.expo, openai.RateLimitError)
        def _call():
            self.context.append({"role": "user", "content": user_input})
            response = openai.chat.completions.create(
                model=self.model, messages=self.context
            )
            ai_message = response.choices[0].message.content
            self.context.append({"role": "assistant", "content": ai_message})
            return ai_message

        return _call()


class AnthropicAgent:
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
        import anthropic

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.context = []

    def interact(self, user_input):
        msg = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=self.context + [{"role": "user", "content": user_input}],
            max_tokens=8192,
        )
        ai_message = msg.content[0].text  # type: ignore
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": ai_message})
        return ai_message


class GeminiAgent:
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        api_key=None,
        system_prompt="""You are an expert AI agent designed to solve physics problems by interacting directly with a physics simulator. You have access to a variety of tools to manipulate objects, query object states (position, velocity, acceleration, etc.), and simulate physics progression through time (step).

Here are some important guidelines for interacting with the environment:
1) ALWAYS Provide clear reasoning for every action.
2) ALWAYS return actions formatted as valid JSON arrays of tool calls.
3) Simulate time progression explicitly using the step function.
4) Query the object states to give you better context of the environment, it will not automatically tell you this.

Submit your answer only when confident, using the answer function.""",
    ):
        import google.generativeai as genai
        from google.generativeai.generative_models import GenerativeModel
        from google.generativeai.client import configure

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        configure(api_key=self.api_key)
        self.model = GenerativeModel(model_name=model_name)
        self.system_prompt = system_prompt
        self.context = []

    def interact(self, user_input):
        prompt = "System: " + self.system_prompt + "\n"
        for msg in self.context:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        prompt += f"User: {user_input}\nAssistant:"
        response = self.model.generate_content(
            prompt, generation_config={"temperature": 0.2, "max_output_tokens": 2048}
        )
        ai_message = response.text
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": ai_message})
        return ai_message


class BaseTogetherAgent:
    def __init__(self, api_key=None, model_name=None, system_prompt=None):
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
        )

        ai_message = response_stream.choices[0].message.content  # type: ignore

        # Update context
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": ai_message})

        return ai_message


# Specific agents with their respective model names


class LlamaAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="meta-llama/Llama-4-Scout-17B-16E-Instruct",
            system_prompt=system_prompt,
        )


class GemmaAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="google/gemma-2-27b-it",
            system_prompt=system_prompt,
        )


class DeepSeekAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="deepseek-ai/DeepSeek-R1",
            system_prompt=system_prompt,
        )


class Llama3370BAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            system_prompt=system_prompt,
        )


class QwenAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="Qwen/Qwen3.5-397B-A17B",
            system_prompt=system_prompt,
        )


class MixtralAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
            system_prompt=system_prompt,
        )


class KimiAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, model_name=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="moonshotai/Kimi-K2.5",
            system_prompt=system_prompt,
        )


class GLMAgent(BaseTogetherAgent):
    def __init__(self, api_key=None, model_name=None, system_prompt=None):
        super().__init__(
            api_key=api_key,
            model_name="zai-org/GLM-5",
            system_prompt=system_prompt,
        )
