# from langchain_groq import ChatGroq
# from langchain.messages import HumanMessage, SystemMessage
# import os
# from dotenv import load_dotenv

# load_dotenv()

# def get_groq_response(user_text: str):
#     """
#     Send user text to Groq LLM and return generated response.
#     """
#     try:
#         llm = ChatGroq(
#             model="openai/gpt-oss-20b",
#             api_key=os.getenv("GROQ_API_KEY"),
#             temperature=0.7,
#             max_tokens=512
#         )

#         system_prompt = (
#             "You are an AI assistant that gives concise, natural voice-like responses. "
#             "Keep your tone friendly and conversational."
#         )

#         messages = [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=user_text)
#         ]

#         # ⚡ Generate response (messages must be wrapped in a list)
#         resp = llm.generate([messages])  # <-- correct usage

#         # Access the generated text
#         generated_text = resp.generations[0][0].text.strip()

#         return generated_text

#     except Exception as e:
#         print("❌ Error in Groq LLM:", e)
#         return "Error generating response."

#added conversation memory
from langchain_groq import ChatGroq
from langchain.messages import HumanMessage, SystemMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Simple global memory
# -------------------------
class SimpleMemory:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.messages = []

    def add(self, role, content):
        if role == "user":
            self.messages.append(HumanMessage(content=content))
        elif role == "ai":
            self.messages.append(AIMessage(content=content))
        # Keep only last `window_size` messages
        self.messages = self.messages[-self.window_size:]

    def get_history(self):
        return self.messages.copy()


# Initialize memory
memory = SimpleMemory(window_size=5)

# -------------------------
# Groq response function
# -------------------------
def get_groq_response(user_text: str):
    """
    Send user text to Groq LLM and return generated response.
    Uses short-term global memory to remember recent conversation.
    """
    try:
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.7
        )

        system_prompt = SystemMessage(
            content="You are an AI assistant that gives concise, natural voice-like responses. "
                    "Keep your tone friendly and conversational."
        )

        # Get previous conversation from memory
        history = memory.get_history()

        # Build message list for LLM
        messages = [system_prompt] + history + [HumanMessage(content=user_text)]

        # Generate response
        resp = llm.generate([messages])
        generated_text = resp.generations[0][0].text.strip()

        # Save current exchange in memory
        memory.add("user", user_text)
        memory.add("ai", generated_text)

        return generated_text

    except Exception as e:
        print("❌ Error in Groq LLM:", e)
        return "Error generating response."


# -------------------------
# Example usage
# -------------------------
# if __name__ == "__main__":
#     print(get_groq_response("Hello, how are you?"))
#     print(get_groq_response("Tell me a joke."))
#     print(get_groq_response("What's the weather today?"))
