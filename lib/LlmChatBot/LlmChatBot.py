from llama_index.llms.openrouter import OpenRouter
llm = OpenRouter(
    api_key="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",
    max_tokens=256,
    context_window=4096,
    model="google/gemma-7b-it:free",
)


class AskChatBot:
    def __init__(self) -> None:
        self.response
    def ask(self, msg):
        self.response = llm.complete(msg)
    def getAnswer(self):
        print(str(self.response))
        return str(self.response)
