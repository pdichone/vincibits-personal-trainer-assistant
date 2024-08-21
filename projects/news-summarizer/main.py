import os
import json
import openai
import requests
import time

import streamlit as st

from dotenv import  load_dotenv


load_dotenv()

news_api_key = os.environ.get("NEWS_API_KEY")
openai.api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI()

model= "gpt-3.5-turbo"

def get_news(topic):
  final_news = []
  url = (
    f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=1&page=1"
  )
  try:
    response = requests.get(url)
    if response.status_code == 200:
      news = json.dumps(response.json(), indent=4)
      news_json = json.loads(news)

      data = news_json

      # Access all the fields == loop through
      status = data['status']
      total_results = data['totalResults']
      articles = data['articles']
   
      
      # Loop through articles
      for article in articles:
        source_name = article['source']['name']
        author = article['author']
        title = article['title']
        description = article['description']
        url = article['url']
        content = article['content']
        tilte_description = f"""
Title: {title}
Author: {author},
Source: {source_name},
Description: {description},
URL: {url}
"""
        final_news.append(tilte_description)   
  except requests.exceptions.RequestException as e:
    print("Error occured during API Request", e)
  return final_news

class AssistantManager:
  assistant_id = None
  thread_id = None

  def __init__(self) -> None:
    self.client = client
    self.assistants = client.beta.assistants
    self.threads = self.client.beta.threads
    self.messages = self.client.beta.threads.messages
    self.runs = self.client.beta.threads.runs
    
    self.model = model
    self.assistant = None
    self.thread = None
    self.run = None
    self.summary = None

    # Retrieve existing assistant and thread if IDs are already exist
    if AssistantManager.assistant_id:
      self.assistant = self.client.beta.assistants.retrieve(
          assistant_id=AssistantManager.assistant_id
      )
    if AssistantManager.thread_id:
      self.thread = self.client.beta.threads.retrieve(
          thread_id=AssistantManager.thread_id
      )

  def __str__(self):
    messages = []
    for message in  self.messages.list(thread_id=AssistantManager.thread_id):
      messages.append(str(message))
    return (
      f"AssistantManager State:\n"
      f"Assistant ID: {AssistantManager.assistant_id}\n"
      f"Thread ID: {AssistantManager.thread_id}\n"
      f"Model: {self.model}\n"
      f"Assistant: {self.assistant}\n"
      f"Thread: {self.thread}\n"
      f"Messages: {messages}\n"
      f"Run: {self.run}\n"
      f"Summary: {self.summary}\n"
    )

  def create_assistant(self, name, instractions, tools):
    if not self.assistant:
      assistant_obj = self.assistants.create(
        name=name,
        instructions=instractions,
        tools=tools,
        model=self.model
      )

      # Save the assistant ID
      AssistantManager.assistant_id = assistant_obj.id
      self.assistant = assistant_obj
      print(f"Assistant ID::: {self.assistant.id}")

  def create_thread(self):
    if not self.thread:
      thread_obj = self.threads.create()
      AssistantManager.thread_id = thread_obj.id
      self.thread = thread_obj
      print(f"ThreadID::: {self.thread.id}")
  
  def add_message_to_thread(self, role, content):
    if self.thread:
      self.messages.create(
        thread_id=self.thread.id,
        role=role,
        content=content
      )

  def run_assistant(self, instructions):
    if self.thread and self.assistant:
      self.run = self.runs.create(
        thread_id=self.thread.id,
        assistant_id=self.assistant.id,
        instructions=instructions
      )

  def process_message(self):
    if self.thread:
      messages = self.messages.list(
        thread_id=self.thread.id
      )
      summary = []

      last_message = messages.data[0]
      role = last_message.role
      responce = last_message.content[0].text.value
      summary.append(responce)

      self.summary = "\n".join(summary)
      print(f"SUMMERY---> {role.capitalize()}: ==> {responce}")

      # for msg in messages:
      #   role = msg.role
      #   content = msg.content[0].text.value
      #   print(f"SUMMERY---> {role.capitalize()}: ==> {content}")

  # for streamlit
  def get_summary(self):
    return self.summary

  def call_required_functions(self, required_actions):
    if not self.run:
      return
    tool_outputs = []

    for action in required_actions['tool_calls']:
      func_name = action['function']['name']
      arguments = json.loads(action['function']['arguments'])

      if func_name == 'get_news':
        output = get_news(topic=arguments['topic'])
        print(f"STUFFF;;; {output}")
        final_str = ''
        for item in output:
          final_str += ''.join(item)
        
        tool_outputs.append({'tool_call_id': action['id'], 'output': final_str})
      else:
        raise ValueError(f"Unkown function: {func_name}")
    
    print('Submitting outputs back to the Assistant...')
    self.runs.submit_tool_outputs(
      thread_id=self.thread.id,
      run_id=self.run.id,
      tool_outputs=tool_outputs
    )


  def wait_for_completion(self):
    if self.thread and self.run:
      while True:
        time.sleep(5)
        run_status = self.runs.retrieve(
          thread_id=self.thread.id,
          run_id=self.run.id
        )
        print(f"RUN STATUS:: {run_status.model_dump_json(indent=4)}")

        if run_status.status == 'completed':
          self.process_message()
          break
        elif run_status.status == "requires_action":
          print("FUNCTION CALLING NOW...")
          self.call_required_functions(
            required_actions=run_status.required_action.submit_tool_outputs.model_dump()
          )


  #Run the steps
  def run_steps(self):
    run_steps = self.client.beta.threads.runs.steps.list(
      thread_id=self.thread.id,
      run_id=self.run.id
    )
    print(f"Run-Steps::: {run_steps}")
    return run_steps

def main():
  manager = AssistantManager()

  # Streamlit interface
  st.title("News Summarzer")

  with st.form(key='user_input_form'):
    instructions_for_summarize = st.text_input('Enter topic:',value='blockchain')
    submit_button = st.form_submit_button(label='Run Assistant')
    if submit_button:
      manager.create_assistant(
        name = 'News Summarizer',
        instractions="You are a personal article summarizer Assistant who knows how to take a list of article's titles and descriptions and then write a short summary of all the news articles",
        tools = [
          {
            'type': 'function',
            'function': {
              'name': 'get_news',
              'description': 'Get the list of articles/news for the given topic',
              'parameters': {
                'type': 'object',
                'properties': {
                  'topic': {
                    'type': 'string',
                    'description': 'The topic for the news, e.g. bitcoin'
                  }
                },
                'required': ['topic'],
              },
            }
          }
        ]
      )

      manager.create_thread()

      # Add the message and run the assistant
      manager.add_message_to_thread(
        role='user',
        content=f"Summarize the news on this topic: {instructions_for_summarize}"
      )

      manager.run_assistant(
        instructions='Summarize the news'
      )


      # Wait for completins and process messages
      manager.wait_for_completion()
      summary = manager.get_summary()

      st.write(summary)
      st.text('Run steps:')
      st.code(manager.run_steps(), line_numbers=True)


if __name__ == '__main__':
  main()