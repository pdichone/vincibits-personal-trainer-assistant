import os
import openai
import time
import logging

from dotenv import  load_dotenv
from datetime import datetime

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

client = openai.OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY")
)

model= "gpt-3.5-turbo"

# === Hardcode our ids ===
assistant_id = "asst_e8Vffgoqbm6B6n91iBjAag40"

thread_id = "thread_kRnEBC7EUgU5dgsPJXF0TkfW"

# === Create a Message ===
message = "What is the best way to be the best in Math?"

message = client.beta.threads.messages.create(
  thread_id=thread_id,
  role="user",
  content=message
)

# === Run our Assistant ===

run = client.beta.threads.runs.create(
  thread_id=thread_id,
  assistant_id=assistant_id,
  instructions="Please, address thr user as James Bond"
)
run_id = run.id

def wait_for_run_competition(client, thread_id,run_id,sleep_interval=5):
  """
  Waits for a run to complete and prints the elapsed time:param client: The Op
  :param thread_id: The ID of the thread.
  :param run_id: The ID of the run.
  :param sleep_interval: Time in seconds to wait between checks.
  """

  while True:
    try:
      run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
      if run.completed_at:
        elapsed_time = run.completed_at - run.created_at
        formatted_elapsed_time = time.strftime(
            "%H:%M:%S", time.gmtime(elapsed_time)
        )
        print(f"Run completed in {formatted_elapsed_time}")
        logging.info(f"Run completed in {formatted_elapsed_time}")
        # Get message here once Run is completed!
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        last_message = messages.data[0]
        response = last_message.content[0].text.value
        print(f"Assistant Response: {response}")
        break
    except Exception as e:
      logging.error(f"An error occurred while retrieving the run: {e}")
      break  
    logging.info("Waiting for run to complete...")
    time.sleep(sleep_interval)

    # === Run ===

wait_for_run_competition(client=client, thread_id=thread_id, run_id=run_id)

# === Steps --- Logs ==
run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run_id)