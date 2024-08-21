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
assis_id = 'asst_yfs8VQTr3xSvQTmH1T87Diuo'
print(assis_id)
# thread_obj = 'thread_pXcEuHU44k9yJecqxnJzHgW4'

# == Step 3. Create a Thread
message = "What is mining?"


thread = client.beta.threads.create()
thread_id = thread.id
print(thread_id)

summary = ''

## == Run the Assistant
run = client.beta.threads.runs.create(
  thread_id=thread_id,
  assistant_id=assis_id,
  instructions='Please address the user as Bruce'
)

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
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_message = messages.data[0]
        response = last_message.content[0].text.value
        print(f"Assistant Response: {response}")
        break
    except Exception as e:
      logging.error(f"An error occurred while retrieving through {e}  ")
      break
    logging.info('Waiting for run to complete...')
    time.sleep(sleep_interval)

# === Run it
wait_for_completion(client=client,thread_id=thread_id,run_id=run.id)

# === Check the Run Steps - LOGS ===
run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id,run_id=run.id)
print(f"Run Steps --> {run_steps.data[0]}")