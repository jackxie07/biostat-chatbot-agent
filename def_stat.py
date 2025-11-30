import json

def find_stat_method(user_input, chat_history, client):
    """
    Identify statistical method according to user's input
    """
    with open("standard_analysis_schema.json", "r") as f:
        standard_analysis_schema = json.load(f)

    macro_names = set()
    for key, value in standard_analysis_schema["properties"].items():
        macro_names.add(value["name"])

    # Append the user input to the chat history
    prompt = f"Here is the list of available analysis: {macro_names}.\nPlease refer to following detailed description: {standard_analysis_schema}\nBased on user's input: {user_input} \nWhich (if any) of the available analysis is the user requesting?\nReturn only the name of the analysis, no other description.\nIf the requested analysis is not in the list, return a value of 0.\n"
    chat_history.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        messages=chat_history,
        model="llama3-70b-8192",
        response_format={"type": "text"},
    )

    # Append the response to the chat history
    chat_history.append(
        {"role": "assistant", "content": chat_completion.choices[0].message.content}
    )

    return chat_completion.choices[0].message.content, chat_history

def find_stat_param():
    """
    Identify statistical parameter according to user's input
    """
    # check current json status which parameter is missing

    # find the first missing parameter

    # return sentences to ask for user input

def check_what_is_empty(user_analysis_details):
    """
    Check for the fields of AnalysisDetails class that are empty. This list will be used to fill all missing fields.
    """
    ask_for = []

    # Note: AnalysisDetails() class can be converted to dictionary, maybe we can use dictionary directly?
    for field, value in user_analysis_details.items():
        if value in [None, "", 0, ]:  # You can add other 'empty' conditions as per your requirements.
            print(f"Field '{field}' is empty.")
            ask_for.append(f"{field}")

    return ask_for

def add_non_empty_details(current_details, new_details):
    """
    Checking the response and add the non-empty information to the AnalysisDetails dict.
    """
    non_empty_details = {k: v for k, v in new_details["properties"].items() if v["value"] not in [None, ""]}
    updated_details = current_details.copy(update=non_empty_details)
    return updated_details

def add_new_details(current_details, new_details):
    """
    Checking the response and add the new information to the AnalysisDetails dict.
    """
    updated_details = current_details.copy()
    for key, value in updated_details.items():
        if value in [None, ""] and new_details[key] not in [None, ""]:
            updated_details[key] = new_details[key]

    return updated_details

def ask_for_info(ask_for, llm, chat_history=[]):
    """
    Ask information sequentially for all parameters needed. We will first construct the prompt and gather collect all information through the chain.
    """
    # prepare prompt template 1
    first_prompt = f"Below are some things to ask the user for in a conversational and natural way. You should only ask one question at a time even if you don't get all the info \
        don't ask as a list! Don't greet the user! Don't say Hi. Explain you need to get some info from the user to run the analysis. Don't repeat that you need get info from the user. If the ask_for list is empty then thank them and ask how you can help them \n\n \
        ### ask_for list: {ask_for}"

    # define `info_gathering_chain`: LLM Chain to collect information through the AI chat
    ai_chat = LLMChain(llm=llm, prompt=first_prompt, chat_history=chat_history)
    
    return ai_chat

def LLMChain(llm, prompt, chat_history=[]):
    """
    Allow user to chain multiple prompts and responses together to create a conversation flow.
    """

    # Append the user input to the chat history
    chat_history.append({"role": "user", "content": prompt})

    chat_completion = llm.chat.completions.create(
        messages=chat_history,
        model="llama3-70b-8192",
        response_format={"type": "text"},
    )

    # Append the response to the chat history
    chat_history.append(
        {"role": "assistant", "content": chat_completion.choices[0].message.content}
    )

    return chat_completion.choices[0].message.content, chat_history