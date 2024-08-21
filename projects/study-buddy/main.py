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

# Get all file from the list

filename = 'cryptocurrency.pdf'
if 'clean_old_files' not in st.session_state:

  # Delete all files with "cryptocurrency.pdf" as a name
  while True:
    files = client.files.list()
    study_buddy_files = [file for file in files if file.filename == filename]
    
    if not study_buddy_files:
        print(f"All '{filename}' files have been deleted.")
        break
    for file in study_buddy_files:
          client.files.delete(file.id)
          print(f"Deleted file: {file.filename} with ID: {file.id}")
  st.session_state['clean_old_files'] = True

# Delete all Vector stores with name "Study Buddy"
vector_store_name = 'Study Buddy'
if 'clean_old_vector_stores' not in st.session_state:
  while True:
      vector_stores = client.beta.vector_stores.list()
      
      # Фильтруем ассистентов с именем 'Study Buddy'
      study_buddy_vector_stores = [store for store in vector_stores if store.name == vector_store_name]

      if not study_buddy_vector_stores:
        print(f"All '{vector_store_name}' Vector stores have been deleted.")
        vector_store = client.beta.vector_stores.create(name="Study Buddy")
        st.session_state['vector_store'] = vector_store
        break
      for store in study_buddy_vector_stores:
          client.beta.vector_stores.delete(store.id)
          print(f"Deleted Vector Store: {store.name} with ID: {store.id}")
  st.session_state['clean_old_vector_stores'] = True


# Create a vector store caled "Financial Statements"


# Step 1. Upload a file to OpenAI embeddings ===
filepath = filename
file_tuple = None
# file=open(filepath, 'rb')
# file_tuple = (filepath, file)

assis_id = 'asst_4lPMEcjTv05KagaWx9ai4Fkg'
thread = client.beta.threads.create()
thread_id = thread.id

# Initialize all the session
if 'file_tuple_list' not in st.session_state:
  st.session_state['file_tuple_list'] = []

if 'start_chat' not in st.session_state:
  st.session_state['start_chat'] = False

if 'thread_id' not in st.session_state:
  st.session_state['thread_id'] = None

# Set up our front end page
st.set_page_config(
  page_title='Study Buddy - Chat and Learn',
  page_icon=':books:'
)

# === Function definitions etc ===

def upload_to_openai(filepath):
  file = open(filepath, 'rb')
  file_tuple = (filepath, file)
  return file_tuple  

# === Sidebar - where users can upload files
file_uploaded = st.sidebar.file_uploader(
  'Upload a file to be transformed into embedings', key = 'file_upload'
)

# Upload file button - store the file ID
if st.sidebar.button('Upload File'):
  if file_uploaded:
    # with open(f"{file_uploaded.name}", 'wb') as f:
    #   f.write(file_uploaded.getbuffer())
    file_tuple = upload_to_openai(f"{file_uploaded.name}")
    st.session_state['file_tuple_list'].append(file_tuple)
    # st.sidebar.write(f"File ID:: {another_file_id}")

# Display those file ids
if st.session_state['file_tuple_list']:
  
  for file_tuple in st.session_state['file_tuple_list']:
    vector_store = st.session_state['vector_store']
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
      vector_store_id = vector_store.id, 
      files=[file_tuple]
    )
    while file_batch.status != 'completed':
      print(file_batch.status)
    
    st.sidebar.write(f"File '{file_tuple[0]}' is uploaded")  
  

  client.beta.assistants.update(
    assis_id,
    tools=[{"type": "file_search"}],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
  )  
  
 
# Button to initiate the chat session
if st.sidebar.button('Start Chatting...'):
  if st.session_state['file_tuple_list']:
    st.session_state['start_chat'] = True
   
    # Create a new thead for this chat session
    chat_thread = client.beta.threads.create()
    st.session_state['thread_id'] = chat_thread.id
    st.write('Thread ID:', chat_thread.id)
  else:
    st.warning('No files found. Please, upload at least one file to get started.')

def process_message_with_citations(message):
  """Extract content and annotations from message and format citations as footnotes."""
  message_content = message.content[0].text
  annotations = (
    message_content.annotations if hasattr(message_content, 'annotations') else []
  )
  citations = []

  # Iterate over the annotations and add footnotes
  for index, annotation in enumerate(annotations):
    # Replace the text with a footnote
    message_content.value = message_content.value.replace(
      annotation.text, f" [{index + 1}]"
    )
    # Gather citations based on annotation attributes
    if file_citation := getattr(annotation, 'file_citation', None):
      # Retrieve the cited file details 
      cited_file = {
        'filename': 'cryptocurrency.pdf'
      } # this should be replaced with acutal file retrieval
      citations.append(
        f"[{index + 1}] {file_citation.quote} from {cited_file['filename']}"
      )

    elif filepath := getattr(annotation, 'file_path', None):
      # Pathholder for file download citation
      cited_file = {
        'filename': 'cryptocurency.pdf'
      } # TODO: this should be replaced with actual file retrival
    
    citations.append(
      f"[{index + 1}] Click [here](#) to download {cited_file['filename']}"
    ) # The download link should be replaced with actual dowload

  # Add footnotes to the end of the message content
  full_responce = message_content.value + '\n\n' + '\n'.join(citations)
  return full_responce


# the main interface ...
st.title('Study Buddy')
st.write('Learn fast by chatting with your documents')

# Check sessions
if st.session_state['start_chat']:
  st.info('Hello')
  if 'openai_model' not in st.session_state:
    st.session_state['openai_model'] = model

  if 'messages' not in st.session_state:
      st.session_state.messages = []


  # Show existing messages
  for message in st.session_state['messages']:
    with st.chat_message(message['role']):
      st.markdown(message['content'])

  # chat input for the user
  if prompt := st.chat_input("What's new?"):
    # Add usermessage
    st.session_state['messages'].append({
      'role': 'user',
      'content': prompt
    })
    with st.chat_message('user'):
      st.markdown(prompt)

    # Add the user's message to the existing thread
    client.beta.threads.messages.create(
      thread_id=st.session_state['thread_id'],
      role='user',
      content=prompt
    )

    # Creat and run with additional instructions
    run = client.beta.threads.runs.create(
      thread_id=st.session_state['thread_id'],
      assistant_id=assis_id,
      instructions=(
        'Please answer the questions using the knowledge, questions using the knowledge provided in the files, '
        'when adding additional information, make sure to distinguish it with bold or underlined text.'
        )
    )

    # Show a spinner while the assistant is thinking.
    with st.spinner('Wait ... Generating response...'):
      while run.status != 'completed':
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
          thread_id=st.session_state['thread_id'],
          run_id=run.id
        )

    # Retrieve messages added by the assistant
    messages =client.beta.threads.messages.list(
      thread_id=st.session_state['thread_id'],
    )

    # Process and display assistant message

    assistant_messages_for_run = [
      message for message in messages
      if message.run_id == run.id and message.role == 'assistant'
    ]

    for message in assistant_messages_for_run:
      full_response = process_message_with_citations(message)
      st.session_state['messages'].append(
        {
          'role':'assistant',
          'content':full_response}
        )
      with st.chat_message('assistant'):
        st.markdown(full_response, unsafe_allow_html=True)
else:
  # Prompt users to star chat
  st.write('Please, upload at least a file to get started by clicking on the "Start Chatting..." button')
