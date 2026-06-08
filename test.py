from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
import os

load_dotenv()

model = ChatDeepSeek(model="deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))

response = model.invoke("What is the weather in Tokyo?")

print(response)