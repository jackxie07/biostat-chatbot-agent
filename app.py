# Import necessary libraries
import markdown
from flask import Flask, render_template, request, redirect
from orchestrator_service import OrchestratorAgent
import os
import time
# import llm_db

## Original Chatbot Set up
# # Set the OpenAI API key
# openai.api_key = "OPENAI_API"
#
# # Define the name of the bot
# name = 'BOT'
#
# # Define the role of the bot
# role = 'customer service'
#
# # Define the impersonated role with instructions
# impersonated_role = f"""
#     From now on, you are going to act as {name}. Your role is {role}.
#     You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
#     Forward them to the website for more information.
#     YOU ARE NOT AN AI MODEL!
# """

orchestrator = OrchestratorAgent(model_name="gemini-1.5-flash", user_name="songgu.xie")
biostat_chatbot = orchestrator.core

print("Initialization:\n")

print(biostat_chatbot.api_key)
print(biostat_chatbot.model_name)
print(biostat_chatbot.chat_history)

# Initialize variables for chat history
explicit_input = ""
chatgpt_output = 'Chat log: /n'
cwd = os.getcwd()
i = biostat_chatbot.session_id

# # Find an available chat history file
# while os.path.exists(os.path.join(cwd, f'chat_history{i}.txt')):
#     i += 1

history_file = os.path.join(cwd, f'chat_history/chat_history{i}.txt')
print(history_file)

# Create a new chat history file
with open(history_file, 'w') as f:
    f.write('\n')

# Initialize chat history
chat_history = ''

# Create a Flask web application
app = Flask(__name__)

# # Function to complete chat input using OpenAI's GPT-3.5 Turbo
# def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
#     output = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo-0301",
#         temperature=1,
#         presence_penalty=0,
#         frequency_penalty=0,
#         max_tokens=2000,
#         messages=[
#             {"role": "system", "content": f"{impersonated_role}. Conversation history: {chat_history}"},
#             {"role": "user", "content": f"{user_input}. {explicit_input}"},
#         ]
#     )
#
#     for item in output['choices']:
#         chatgpt_output = item['message']['content']
#
#     return chatgpt_output
#
# # Function to handle user chat input
# def chat(user_input):
#     global chat_history, name, chatgpt_output
#     current_day = time.strftime("%d/%m", time.localtime())
#     current_time = time.strftime("%H:%M:%S", time.localtime())
#     chat_history += f'\nUser: {user_input}\n'
#     chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
#     chatgpt_output = f'{name}: {chatgpt_raw_output}'
#     chat_history += chatgpt_output + '\n'
#     with open(history_file, 'a') as f:
#         f.write('\n'+ current_day+ ' '+ current_time+ ' User: ' +user_input +' \n' + current_day+ ' ' + current_time+  ' ' +  chatgpt_output + '\n')
#         f.close()
#     return chatgpt_raw_output
#
# # Function to get a response from the chatbot
# def get_response(userText):
#     return chat(userText)

# Define app routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
# Function for the bot response
def get_bot_response():

    user_input = request.args.get('msg')
    ai_response = orchestrator.handle_message(user_input)

    html = markdown.markdown(ai_response)
    return str(html)

@app.route('/refresh')
def refresh():
    time.sleep(600) # Wait for 10 minutes
    return redirect('/refresh')

# Run the Flask app
if __name__ == "__main__":
    app.run()
