import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY"),  # type: ignore
    model_name="meta-llama/llama-4-scout-17b-16e-instruct",
)
