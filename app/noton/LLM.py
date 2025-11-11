import time
from openai import OpenAI
from noton.Module import Module

class LLM(Module):
    def __init__(self) -> None:
        super().__init__()

class Ollama(LLM):
    def __init__(self, base_url=None, api_key = None, model=None, image_url=None, user_prompt=None, system_prompt=None, retry_attempts=10, retry_interval=15, enable_history=True) -> None:
        super().__init__()
        self.base_url_ = base_url
        self.api_key_ = api_key
        self.model_ = model
        self.image_url_ = image_url
        self.user_prompt_ = user_prompt
        self.system_prompt_ = system_prompt
        self.retry_attempts_ = max( retry_attempts, 1 )
        self.retry_interval_ = max( retry_interval, 1 )
        self.enable_history_ = enable_history

        self.conversation_history_ = []  # to store the conversation history if needed

    def forward(self, user_prompt=None, system_prompt=None, base_url=None, api_key=None, model=None, image_url=None) -> str | None:
        # defaults to the instance variables if not provided
        user_prompt = user_prompt if user_prompt is not None else self.user_prompt_
        system_prompt = system_prompt if system_prompt is not None else self.system_prompt_
        base_url = base_url if base_url is not None else self.base_url_
        api_key = api_key if api_key is not None else self.api_key_
        api_key = api_key if api_key is not None else 'ollama'
        model = model if model is not None else self.model_
        image_url = image_url if image_url is not None else self.image_url_

        assert user_prompt is not None, "user_prompt must be provided"
        assert base_url is not None, "base_url must be provided"
        assert model is not None, "model must be provided"

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if image_url is not None and image_url.strip() != "":
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [{"type":"text", "text":user_prompt}, {"type":"image_url", "image_url": {"url": image_url}}]},
            ]

        self.conversation_history_.extend(messages)


        for attempt in range(self.retry_attempts_):
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create( model=model, messages=self.conversation_history_,)
                ans = response.choices[0].message.content
                if self.enable_history_:
                    self.conversation_history_.append({"role": "assistant", "content": ans})
                return ans

            except Exception as e:
                print(f"Error during LLM call: {str(e)}")
                if self.retry_interval_ > 0 and attempt < self.retry_attempts_ - 1:
                    time.sleep(self.retry_interval_)
                else:
                    return None


if __name__ == '__main__':
    ollama = Ollama(
        base_url="http://10.147.19.168:10027/v1",
        model="gemma3:27b",
        system_prompt="You are a helpful assistant."
    )
    response = ollama.forward(user_prompt="What is the capital of France?")
    print("Response:", response)
    response = ollama.forward(user_prompt="And what is it famous for?")
    print("Response:", response)


    ollama = Ollama(
        base_url="https://openrouter.ai/api/v1",
        model="minimax/minimax-m2:free",
        system_prompt="You are a helpful assistant."
    )
    response = ollama.forward(user_prompt="What is the capital of France? What is it famous for?")
    print("Response:", response)







