import logging
import os
import time
import openai
import streamlit as st

from dotenv import  load_dotenv
from datetime import datetime


load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

client = openai.OpenAI()

model= "gpt-3.5-turbo"


def wait_for_completion(client,thread_id, run_id, sleep_interval=5):
  """
  Waits for a run to complete and prints the elapsed time:parm
  :param thread_id: The ID of the thread.
  :param run_id: The ID of the run.
  :param sleep_interval: Time in seconds to wait between checks.
  """

  while True:
    try:
      run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
      )
      
      if run.completed_at:
        elapsed_time = run.completed_at - run.created_at
        formatted_elapsed_time = time.strftime(
          "%H:%M:%S", time.gmtime(elapsed_time)
        )
        print(f"Run completed in {formatted_elapsed_time}")
        logging.info(f"Run completed in {formatted_elapsed_time}")

        # Get messages here once Run is completed!
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        last_message = messages.data[0]
        response = last_message.content[0].text.value
        print(f"Assistant Response: {response}")
        break
    except Exception as e:
      logging.error(f"An error occurred while retrieving through {e}  ")
      break
    logging.info('Waiting for run to complete...')
    time.sleep(sleep_interval)


# Step 1. Upload a file to OpenAI embeddings ===
filepath = 'cryptocurrency.pdf'
file=open(filepath, 'rb')
file_tuple = (filepath, file)
# file_object = client.files.create(file=file, 
#                                   purpose='assistants')

# Get all file from the list
files = client.files.list()

# Delete all files with "cryptocurrency.pdf" as a name
for file in files:
    if file.filename == 'cryptocurrency.pdf':
        client.files.delete(file.id)
        print(f"Deleted file: {file.filename} with ID: {file.id}")

# get all Vector stores
vector_stores = client.beta.vector_stores.list()

# Delete all Vector stores with name "Study Buddy"
for store in vector_stores:
    if store.name == 'Study Buddy':
        client.beta.vector_stores.delete(store.id)
        print(f"Deleted Vector Store: {store.name} with ID: {store.id}")


# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Study Buddy")
print(vector_store)

# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=[file_tuple]
)

while file_batch.status != 'completed':
  print(file_batch.status)

# Предполагается, что клиент уже инициализирован
# client = openai.Client(api_key="your-api-key")

while True:
    assistants = client.beta.assistants.list()
    
    # Фильтруем ассистентов с именем 'Study Buddy'
    study_buddy_assistants = [assistant for assistant in assistants if assistant.name == 'Study Buddy']
    
    if not study_buddy_assistants:
        print("All 'Study Buddy' assistants have been deleted.")
        break
    
    for assistant in study_buddy_assistants:
        client.beta.assistants.delete(assistant.id)
        print(f"Deleted assistant with ID: {assistant.id} and name: '{assistant.name}'")


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

tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
  model=model,

)

# === Get the Assis ID ===
assis_id = assistant.id
# # thread_id = 'thread_r7JrMQ1GPEaQLpHFtw1UgU5A'

# == Step 3. Create a Thread
message = "What is mining?"


thread = client.beta.threads.create()
thread_id = thread.id
# print(thread_id)

message = 'What is mining?'

message = client.beta.threads.messages.create(
   thread_id=thread_id,
   role='user',
   content=message
)

## == Run the Assistant
run = client.beta.threads.runs.create(
  thread_id=thread_id,
  assistant_id=assis_id,
  instructions='Please address the user as Bruce'
)

# === Run it
wait_for_completion(client=client,thread_id=thread_id,run_id=run.id)

# # === Check the Run Steps - LOGS ===
# run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id,run_id=run.id)
# print(f"Run Steps --> {run_steps.data[0]}")