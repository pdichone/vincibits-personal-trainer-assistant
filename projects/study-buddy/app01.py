import os
import openai
import streamlit as st

from dotenv import  load_dotenv
from datetime import datetime


load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

client = openai.OpenAI()

model= "gpt-3.5-turbo"


# Step 1. Upload a file to OpenAI embeddings ===
filepath = 'cryptocurrency.pdf'
file_object = client.files.create(file=open(filepath, 'rb'), 
                                  purpose='assistants')
# Step 2 - Create an assistant
assistant = client.beta.assistants.create(
  name='Study Buddy', 
  instructions="""You are a helpful study assistant who knows a lot about understanding research papers.
  Your role is to summarize papers, clarify terminology whithin context, and extract key figures and data.
  Cross-reference information for additional insights and answer related questions comprehensively.
  Analize the papers, noting strengths and limitations.
  Handle data securely and update your knowledge base with the latest research.
  Adhere to ethical standards, respect inerllecutual property, and provide users with guidance on any limitations.
  Maintain a feedpack looop for continuous improvement and user support.
  Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible.
""",
tools=[{'type': 'file_search'}],
model=model,
# file_ids=[file_object.id]
)

# === Get the Assis ID ===
assis_id = assistant.id
print(assis_id)

thread_obj = client.beta.threads.create()
thread_id = thread_obj.id
print(thread_id)