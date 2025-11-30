import os
from datetime import datetime

from groq import Groq
import google.generativeai as genai
import json
import random

# TODO Remove local database connection and update with online version in the future
# import llm_db

import SASConnect
import llm_db

# from main import user_details
# from main import user_details

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class _GeminiChatCompletions:
    """
    Lightweight adapter to mimic the Groq/OpenAI .chat.completions.create interface.
    """

    class _ResultWrapper:
        class _MsgWrapper:
            def __init__(self, content):
                self.content = content

        class _ChoiceWrapper:
            def __init__(self, content):
                self.message = _GeminiChatCompletions._ResultWrapper._MsgWrapper(content)

        def __init__(self, content):
            self.choices = [self._ChoiceWrapper(content)]

    def __init__(self, model):
        self.model = model

    def create(self, messages, model=None, response_format=None):
        prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])

        # Guide Gemini to return JSON when requested
        if response_format and response_format.get("type") in {"json_object", "json_schema"}:
            system_hint = "Return JSON only, no extra text."
            prompt = f"{system_hint}\n{prompt}"

        resp = self.model.generate_content(prompt)
        content = resp.text if hasattr(resp, "text") else str(resp)
        return self._ResultWrapper(content)


class GeminiClient:
    """
    Adapter exposing .chat.completions.create to align with existing code paths.
    """
    def __init__(self, api_key, model_name="gemini-1.5-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)
        self.chat = type("chat", (), {"completions": _GeminiChatCompletions(self._model)})


def convert(string):
    """
    Python code to convert string to list
    """
    lst = list(string.split(","))
    return lst


class BiostatChatbot:

    ##-------------##
    ## Constructor ##
    ##-------------##

    def __init__(self, api_key, model_name, user_name):
        self.api_key = api_key
        self.model_name = model_name
        if model_name == "llama3-70b-8192":
            self.llm = Groq(api_key=GROQ_API_KEY)
        else:
            # default to Gemini
            self.llm = GeminiClient(api_key=GEMINI_API_KEY, model_name=model_name)

        # Set the system prompt
        system_prompt = {
            "role": "system",
            "content":
                "You are expert SAS programmer with lots of clinical trial domain and statistical analysis knowledge.",
        }
        # Initialize the chat history
        # TODO Remove local database connection and update with online version in the future
        # llm_db.create_session()
        self.user_name = user_name
        self.chat_history = [system_prompt]
        self.analysis_detail = None
        self.analysis_schema = None
        self.analysis_schema_info = None
        self.info_complete = False
        self.confirm_proceed = False
        self.session_id = self.get_session()

    ##-------------------##
    ## Utility Functions ##
    ##-------------------##

    def __str__(self):
        """
        Return a string representation of the BiostatChatbot object, including LLM and analysis information.
        """
        return (f"\nLLM Information:\n"
                f"\nLLM: {self.llm}\n"
                f"Model Name: {self.model_name}\n"
                f"\nAnalysis Information:\n"
                f"\nUsername: {self.user_name}\n"
                f"Analysis Detail: {self.analysis_detail}\n"
                f"Analysis Schema: {self.analysis_schema}\n"
                f"Information Complete: {self.info_complete}\n"
                f"Confirm Proceed: {self.confirm_proceed}\n")

    def get_method(self):
        if self.analysis_detail is not None:
            return self.analysis_detail["AnalysisMethod"]
        else:
            return None

    def get_param(self):
        if self.analysis_detail is not None:
            param_list = []
            for param in self.analysis_detail['Parameters'].keys():
                param_list.append(param)
            return param_list
        else:
            return None

    def get_session(self):
        # TODO Remove local database connection and update with online version in the future
        # return llm_db.get_current_session()
        # TODO return a random number between 1 - 1000 instead
        # return random.randint(1, 1000)
        now = datetime.now()
        timestamp_string = now.strftime("%Y%m%d%H%M%S")
        # filename = f"data_{timestamp_string}.txt"
        return timestamp_string

    def output_chat_history(self):
        """
        Print the chat history to log file
        """
        f = open("chat_history/chat_history" + str(self.session_id) + ".txt", "w")
        for chat in self.chat_history:
            f.write(chat["role"].title() + ":\n" + chat["content"] + "\n\n")
        f.close()

    def save_chat(self, role, content, db=False):

        if db:
            llm_db.save_chat(role, content)
        else:
            f = open("chat_history/full_chat_history" + str(self.session_id) + ".txt", "a")
            f.write(role.title() + ":\n" + content + "\n\n")


    def print_analysis_info(self):
        """
        Print the analysis details
        """
        print("AnalysisMethod:", self.analysis_detail['AnalysisMethod'])
        print("Parameters:")
        for key, value in self.analysis_detail['Parameters'].items():
            print(f"\t{key}: {value}")

    def add_chat_history(self, role, content):
        """
        Add chat history
        """
        self.chat_history.append({"role": role, "content": content})


    ##-----------------------------------------##
    ## LLM Connection & Conversation Functions ##
    ##-----------------------------------------##

    def llm_text(self, prompt):
        """
        Ask LLM specific prompt and get text response.
        """

        # Append the user input to the chat history
        self.add_chat_history("user", prompt)
        # TODO Remove local database connection and update with online version in the future
        self.save_chat("user", prompt)

        chat_completion = self.llm.chat.completions.create(
            messages=self.chat_history,
            model=self.model_name,
            response_format={"type": "text"},
        )

        # Append the response to the chat history
        self.chat_history.append(
            {"role": "assistant", "content": chat_completion.choices[0].message.content}
        )
        # TODO Remove local database connection and update with online version in the future
        self.add_chat_history("assistant", chat_completion.choices[0].message.content)
        self.save_chat("assistant", chat_completion.choices[0].message.content)

        return chat_completion.choices[0].message.content


    def llm_json(self, prompt):
        """
        Ask LLM specific prompt and get JSON response.
        """

        # Append the user input to the chat history
        self.add_chat_history("user", prompt)
        # TODO Remove local database connection and update with online version in the future
        self.save_chat("user", prompt)

        if self.model_name == "llama3-70b-8192":
            chat_completion = self.llm.chat.completions.create(
                messages=self.chat_history,
                model=self.model_name,
                response_format={"type": "json_object"},
            )
        else:
            chat_completion = self.llm.chat.completions.create(
                messages=self.chat_history,
                model=self.model_name,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "AnalysisDetails",
                        "schema": self.analysis_schema,
                        "strict": True
                    }
                }
            )

        # Append the response to the chat history
        self.chat_history.append(
            {"role": "assistant", "content": chat_completion.choices[0].message.content}
        )
        # TODO Remove local database connection
        self.add_chat_history("assistant", chat_completion.choices[0].message.content)
        self.save_chat("assistant", chat_completion.choices[0].message.content)

        return chat_completion.choices[0].message.content


    def ask_for_info(self, ask_for):
        """
        Ask information sequentially for all parameters needed
        """
        if len(ask_for):
            # when parameter list is not complete
            first_prompt = (f"Below are some things to ask the user for in a conversational and natural way. \n"
                            f"First you should confirm current input by referring to schema: {self.analysis_detail}.\n"
                            f"Please show all current input in bullet points. Please don't show unspecified parameters.\n"
                            f"Second you should ask the user more information.\n"
                            f"You should only ask one question at a time even if you don't get all the info "
                            f"don't ask as a list! \nDon't greet the user! \nDon't say Hi. \n"
                            f"Explain you need to get some info from the user to run the analysis. \n"
                            f"Please provide list of options in bullet points if available. \n"
                            f"It should be shown in the format of '<variable_name>: <variable_label>' or '<paramcd>: <param>'\n"
                            f"Please show <variable_name> and <paramcd> as bold.\n"
                            f"Don't repeat that you need get info from the user. \n"
                            f"If the ask_for list is empty then thank them and ask how you can help them \n\n"
                            f"### ask_for list: {ask_for[0]}")

            # define `info_gathering_chain`: LLM Chain to collect information through the AI chat
            ai_chat = self.llm_text(prompt=first_prompt)
        else:
            if self.confirm_proceed:
                complete_prompt = (f"Below are some things to talk to the user for in a conversational and natural way. \n"
                                f"You have collected all the info and the user has confirmed to proceed."
                                f"Don't ask as a list! \nDon't greet the user! \nDon't say Hi. \n"
                                f"Please tell the user we are running SAS programs to perform the analysis. \n")
            else:
                # when parameter list is complete
                complete_prompt = (f"Below are some things to talk to the user for in a conversational and natural way. \n"
                                f"You have collected all the info."
                                f"Don't ask as a list! \nDon't greet the user! \nDon't say Hi. \n"
                                f"Explain you have collected all info needed from the user to run the analysis. \n"
                                f"And ask the user to review these parameters and update these parameters if needed. \n"
                                f"If no updates needed, we need user's confirmation to proceed. \n"
                                f"Ask user to reply 'Yes' if confirm to proceed, and reply 'No' if there's update needed. \n"
                                f"Please return a readable list for current parameter list: {self.analysis_detail}.")

            # define `info_gathering_chain`: LLM Chain to collect information through the AI chat
            ai_chat = self.llm_text(prompt=complete_prompt)

        # TODO Remove local database connection and update with online version in the future
        # self.add_chat_history("Biostat Chatbot", ai_chat)
        self.save_chat("Biostat Chatbot", ai_chat)

        return ai_chat


    ##----------------------------------##
    ## Step 1: Identify Analysis Method ##
    ##----------------------------------##

    def find_stat_method(self, user_input):
        """
        Identify statistical method according to user's input
        """
        # TODO Remove local database connection and update with online version in the future
        # self.add_chat_history(self.user_name, user_input)
        self.save_chat(self.user_name, user_input)
        with open("schema/standard_analysis_schema.json", "r") as f:
            standard_analysis_schema = json.load(f)

        macro_names = set()
        for analysis in standard_analysis_schema:
            macro_names.add(analysis["AnalysisMethod"])

        # Append the user input to the chat history
        prompt = (f"Here is the list of available analysis: {macro_names}.\n"
                  f"Please refer to following detailed description: {standard_analysis_schema}\n"
                  f"Based on user's input: {user_input} \n"
                  f"Which (if any) of the available analysis is the user requesting?\n"
                  f"Return only the 'AnalysisMethod' of the analysis, no other description.\n"
                  f"If the requested analysis is not in the list, return a value of 0.")

        return self.llm_text(prompt)


    def set_analysis(self, analysis_name):
        """
        Set the analysis detail according to the analysis name
        """
        if analysis_name == 'ANCOVA':
            with open("schema/ancova1_analysis_schema.json", "r") as f:
                analysis_schema = json.load(f)
        elif analysis_name == 'BINARY':
            with open("schema/binary1_analysis_schema.json", "r") as f:
                analysis_schema = json.load(f)
        elif analysis_name == 'TTE':
            with open("schema/tte1_analysis_schema.json", "r") as f:
                analysis_schema = json.load(f)
        else:
            with open("schema/mmrm1_analysis_schema.json", "r") as f:
                analysis_schema = json.load(f)

        self.analysis_schema_info = analysis_schema

        # Prepare analysis schema
        schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
        detail = {"AnalysisMethod": analysis_name, "Parameters": {}}

        for key in analysis_schema['properties']['Parameters'].keys():
            schema["properties"].update({key: {"type": "string"}})
            schema['required'].append(key)
            detail["Parameters"].update({key: ""})
        self.analysis_schema = schema
        self.analysis_detail = detail

        prompt = (
            f"According to user's request, we will run a {analysis_name} analysis. \n"
            f"Please refer to following schema for detailed descriptions: {analysis_schema}."
        )

        return self.llm_text(prompt)

    ##-----------------------------------------##
    ## Step 2: Ask Analysis Specific Questions ##
    ##-----------------------------------------##

    def init_info(self):
        pass


    def evaluate_info_loop(self, text_input, ask_for):
        """
        Ask information sequentially in a loop for all parameters needed.
        """
        new_detail = self.analysis_detail

        if ask_for is None:
            ask_for = self.get_param()

        new_detail = self.analysis_detail

        for key in ask_for:
            ##------------------------##
            ## JSON Response from LLM ##
            ##------------------------##
            # eval_prompt = (f"The user requested the following:\n{text_input}\n"
            #                f"Which (if any) of the available value of {key} is the user requesting?\n"
            #                f"{self.fetch_info(key)}\n"
            #                f"Please write outputs in JSON according to current schema: {self.analysis_detail}.")
            #
            # # define `info_gathering_chain`: LLM Chain to collect information through the AI chat
            # new_detail = self.llm_json(prompt=eval_prompt)

            ##------------------------##
            ## TEXT Response from LLM ##
            ##------------------------##
            # refactor to ask LLM to return text instead of JSON schema
            eval_prompt = (f"The user requested the following:\n{text_input}\n"
                           f"Here is the list of available {key}\n"
                           f"{self.fetch_info(key)}\n"
                           f"Which (if any) of the available {key} is the user requesting?\n"
                           f"Return only the paramcd or variable_name value for the {key}.\n"
                           f"If the requested option is not in the list, return a value of 0."
            )

            new_value = self.llm_text(prompt=eval_prompt)

            # add details to schema programmatically (instead of LLM)
            if new_value != '0':
                new_detail['Parameters'][key] = new_value

        return new_detail


    ##----------------------------------------##
    ## Step 3: Ask for Additional Information ##
    ##----------------------------------------##

    def filter_response(self, text_input, initial_input=False):
        """
        Given user's input, collect information and add these information into AnalysisDetails class.

        Parameters:
        text_input (str): The input text from the user.
        initial_input (bool): Flag to determine if this is the initial input. Default is False.

        Returns:
        tuple: A tuple containing the updated user details and a list of parameters that still need information.
        """
        # TODO Remove local database connection and update with online version in the future
        # self.add_chat_history(self.user_name, text_input)
        self.save_chat(self.user_name, text_input)

        # Decide whether to use loop or not based on parameter
        if initial_input:
            new_detail = self.evaluate_info_loop(text_input, ask_for = self.get_param())
        else:
            # new_detail = self.evaluate_info(text_input)
            self.evaluate_info(text_input)

        # add collected info to the AnalysisDetails class

        # TODO Fix the TypeError: The JSON object must be str, bytes or bytearray, not dict
        if self.info_complete and json.loads(new_detail) == self.analysis_detail:
            self.confirm_proceed = True
            # user_details = self.analysis_detail
            ask_for = []
        else:
            # res = json.loads(new_detail)
            # TODO Check what will happen after removing add_new_details step
            # user_details = self.add_new_details(new_detail)
            ask_for = self.check_what_is_empty()

        return self.analysis_detail, ask_for


    def evaluate_info(self, text_input):
        """
        Ask information sequentially for all parameters needed.

        :param text_input: User input
        """
        # Prepare available parameters list (e.g., endpoints, variables) -> fetch_info()
        ask_for = self.check_what_is_empty()
        if ask_for:
            key = ask_for[0]
            print(f"Parameter: {key}")

        # new_detail = self.analysis_detail

        if not self.info_complete:
            # incomplete status: evaluate user info for new parameter added

            ##------------------------##
            ## JSON Response from LLM ##
            ##------------------------##
            # eval_prompt = (f"The user requested the following:\n{text_input}\n"
            #                f"Which (if any) of the available value is the user requesting?\n"
            #                f"{self.fetch_info(key)}\n"
            #                f"We only need the variable name in the list, not description or labels.\n"
            #                f"If the requested option is not in the list, return a value of 0."
            #                f"Please write response in JSON according to current schema: {self.analysis_detail}.")
            #
            # # TODO if user provided is not in the list, what will happen?
            #
            # new_detail = self.llm_json(prompt=eval_prompt)

            ##------------------------##
            ## TEXT Response from LLM ##
            ##------------------------##
            eval_prompt = (f"The user requested the following:\n{text_input}\n"
                           f"Here is the list of available {key}\n"
                           f"{self.fetch_info(key)}\n"
                           f"Which (if any) of the available {key} is the user requesting?\n"
                           f"Return only the Endpoint Code or Variable Name value for the {key}.\n"
                           f"If the requested option is not in the list, return a value of 0."
            )

            new_value = self.llm_text(prompt=eval_prompt)
            print(f"New Value: {new_value}")

            # add details to schema programmingly (instead of LLM)
            # if new_value != '0':
            if self.check_info(key, new_value):
                print("New value existed!")
                # add to Analysis Details only if the check_info returns True
                self.analysis_detail['Parameters'][key] = new_value
            else:
                # TODO ask LLM to run it again (maybe 3 times)
                # TODO if still not correct, we need to stop the program and tell the user
                pass

        # else:
        #     # Confirm/Update Information:
        #     #   when the information status is complete, user will need to confirm to proceed or update current schema
        #     eval_prompt = (f"The user requested the following:\n{text_input}\n"
        #                    f"\nHere is the list of parameters that can be updated:\n"
        #                    f"{self.fetch_info(placeholder)}"
        #                    f"\nIs the user confirming to execute the analysis or is the user asking to update a parameter?\n"
        #                    f"\nReturn a value of 1 if the user is confirming and would like to execute the analysis.\n"
        #                    f"\nIf the user would like to update a parameter(s), what parameter(s) would the user like to update? Only return the name of the parameter(s).\n"
        #                    f"\nElse return a value of 0")
        #
        #     confirm = self.llm_text(prompt=eval_prompt)
        #     print(confirm)
        #
        #     if confirm == "1":
        #         new_detail = self.analysis_detail
        #     else:
        #         new_detail = self.evaluate_info_loop(text_input)

        return self.analysis_detail

    def check_info(self, key, value):
        """
        Check if the output value is from the list
        """
        if value == '0':
            return False

        if key == "Endpoint":
            for val in self.fetch_info(key):
                if val['Endpoint Code'] == value:
                    return True
        elif key == 'Population' or key == 'Covariate' or key == 'ResponseVariable':
            for val in self.fetch_info(key):
                if val['Variable Name'] == value:
                    return True
        elif key == 'CovarianceMatrix':
            for val in self.fetch_info(key):
                if val['Structure'] == value:
                    return True
        else:
            for val in self.fetch_info(key):
                if val == value:
                    return True
        return False

    def fetch_info(self, ask_for):
        """
        Fetch parameter/variable information
        """
        print(self.analysis_schema)
        if ask_for == "Endpoint":
            with open("schema/dataset_endpoint_schema.json", "r") as f:
                dataset_ept_schema = json.load(f)
                param_lst = []
                for i in range(len(dataset_ept_schema)):
                    param_lst.append({"Endpoint": dataset_ept_schema[i]['param'], "Endpoint Code": dataset_ept_schema[i]['paramcd']})
        elif ask_for == "Population":
            # TODO can we only include population variable
            # with open("dataset_variable_schema.json", "r") as f:
            with open("schema/dataset_population_schema.json", "r") as f:
                # param_lst = json.load(f)
                dataset_pop_schema = json.load(f)
                param_lst = []
                for i in range(len(dataset_pop_schema)):
                    param_lst.append(
                        {"Variable Name": dataset_pop_schema[i]['variable_name'], "Variable Label": dataset_pop_schema[i]['variable_label']})
        elif ask_for == "ResponseVariable":
            # param_lst = self.analysis_schema_info['properties']['Parameters']['ResponseVariable']['ValidValues']
            with open("schema/dataset_rspvar_schema.json", "r") as f:
                # param_lst = json.load(f)
                dataset_rspvar_schema = json.load(f)
                param_lst = []
                for i in range(len(dataset_rspvar_schema)):
                    param_lst.append(
                        {"Variable Name": dataset_rspvar_schema[i]['variable_name'],
                         "Variable Label": dataset_rspvar_schema[i]['variable_label']})
        elif ask_for == "CovarianceMatrix":
            param_lst = self.analysis_schema_info['properties']['Parameters']['CovarianceMatrix']['ValidValues']
        elif ask_for == "Covariate":
            # TODO can we only include covariate variable
            # with open("dataset_variable_schema.json", "r") as f:
            with open("schema/dataset_covariate_schema.json", "r") as f:
                # param_lst = json.load(f)
                dataset_covar_schema = json.load(f)
                param_lst = []
                for i in range(len(dataset_covar_schema)):
                    param_lst.append(
                        {"Variable Name": dataset_covar_schema[i]['variable_name'],
                         "Variable Label": dataset_covar_schema[i]['variable_label']})
        # print(f"Valid Values of '{ask_for}' is {param_lst}.")
        return param_lst

    def check_what_is_empty(self):
        """
        Check for the fields of AnalysisDetails class that are empty. This list will be used to fill all missing fields.
        """
        ask_for = []

        # Note: AnalysisDetails() class can be converted to dictionary, maybe we can use dictionary directly?
        for field, value in self.analysis_detail['Parameters'].items():
            if value in [
                None,
                "",
                0,
                {'type': 'string'}
            ]:  # You can add other 'empty' conditions as per your requirements.
                print(f"Field '{field}' is empty.")
                ask_for.append(f"{field}")

        if not ask_for:
            self.info_complete = True

        return ask_for


    def add_new_details(self, new_details):
        """
        Checking the response and add the new information to the AnalysisDetails dict.
        """
        print("Add New Details:")
        print(new_details)
        if "type" in new_details.keys():
            new_details = new_details["properties"]

        for key, value in self.analysis_detail['Parameters'].items():
            if (
                    value in [None, "", 0]
                    and key in new_details['Parameters'].keys()
                    and new_details['Parameters'][key] not in [None, ""]
            ):
                self.analysis_detail['Parameters'][key] = new_details['Parameters'][key]

        return self.analysis_detail

    def add_new_detail(self, new_details):
        """
        Checking the response and add the new information to the AnalysisDetails dict.

        :param new_details: new parameter value as {key: value} (dict)
        :return
        """
        print(new_details)
        if "type" in new_details.keys():
            new_details = new_details["properties"]

        for key, value in self.analysis_detail['Parameters'].items():
            if (
                    value in [None, ""]
                    and key in new_details.keys()
                    and new_details[key] not in [None, ""]
            ):
                self.analysis_detail['Parameters'][key] = new_details[key]

        return self.analysis_detail

    ##------------------------------------##
    ## Step 4: Confirm/Update Information ##
    ##------------------------------------##

    def update_info(self, text_input):
        """
        Confirm/Update Information
        """
        # TODO update/confirm analysis confirmation
        # TODO Remove local database connection and update with online version in the future
        # self.add_chat_history(self.user_name, text_input)
        self.save_chat(self.user_name, text_input)

        # when the information status is complete, user will need to confirm to proceed or update current schema
        eval_prompt = (f"The user requested the following:\n{text_input}\n"
                       f"\nHere is the list of parameters that can be updated:\n"
                       f"{self.get_param()}"
                       f"\nIs the user confirming to execute the analysis or is the user asking to update a parameter?\n"
                       f"\nReturn a value of 1 if the user is confirming and would like to execute the analysis.\n"
                       f"\nIf the user would like to update a parameter(s), what parameter(s) would the user like to update? Only return the name of the parameter(s).\n"
                       f"\nElse return a value of 0")

        resp = self.llm_text(prompt=eval_prompt)
        print(resp)

        if resp == "1":
            self.confirm_proceed = True
            user_details = self.analysis_detail
            self.analysis_detail["UserID"] = 'songgu.xie'
            self.analysis_detail["SessionID"] = self.session_id
            self.analysis_detail["DateTime"] = datetime.now()
            self.analysis_detail["Confirm"] = 'true'
            ask_for = []
        elif resp == "0":
            # TODO ask user again for clarification
            pass
        else:
            # TODO need to turn resp (parameters to update) to a list
            print(resp)
            ask_for = convert(resp)
            new_detail = self.evaluate_info_loop(text_input, ask_for)

            res = json.loads(new_detail)
            user_details = self.add_new_details(res)
            ask_for = []

        # add collected info to the AnalysisDetails class
        # if self.info_complete and json.loads(new_detail) == self.analysis_detail:
        #     self.confirm_proceed = True
        #     user_details = self.analysis_detail
        #     ask_for = []
        # else:
        #     res = json.loads(new_detail)
        #     user_details = self.add_new_details(res)
        #     ask_for = self.check_what_is_empty()

        return user_details, ask_for

    ##--------------------------##
    ## Step 5: Execute Analysis ##
    ##--------------------------##

    def execute_analysis(self):
        """
        Execute the analysis
        """
        stat_method = self.get_method()
        stat_method_param = self.get_param()
        aws_url = ""

        aws_url = SASConnect.execute_analysis(self.analysis_detail)

        return aws_url

    def present_output(self, aws_url):
        """
        User should be notified that the output is ready, and can be retrieved at a certain location
        """
        # TODO Present URL to users
        response = f"Analysis successfully completed! The output can be found at [Link]({aws_url})"
        self.chat_history.append({"role": "assistant", "content": response})
        self.output_chat_history()
        return response

    ##-----------------------------------------##
    ## Functions Under Development or Obsolete ##
    ##-----------------------------------------##

    def identify_intent(self, user_input):
        """
        Identify the intent of the user (TEMP)
        """
        # TODO update the prompt to include a full list of intents
        with open("schema/standard_analysis_schema.json", "r") as f:
            intent_list = json.load(f)

        prompt = (
            f"Based on user's input: {user_input} \n"
            f"What is the intent of the user? \n"
            f"Please refer to following list of intents: {intent_list}\n"
            f"Return only the name of the intent, no other description. \n"
            f"If the intent is not in the list, return a value of 0."
        )
        return self.llm_text(prompt)


    # def add_non_empty_details(self, new_details):
    #     """
    #     Checking the response and add the non-empty information to the AnalysisDetails dict.
    #     """
    #     non_empty_details = {
    #         k: v
    #         for k, v in new_details["properties"].items()
    #         if v["value"] not in [None, ""]
    #     }
    #     updated_details = current_details.copy(update=non_empty_details)
    #     return updated_details
