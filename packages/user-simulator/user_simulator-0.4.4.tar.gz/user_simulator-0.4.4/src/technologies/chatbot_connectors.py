import json
import uuid
import yaml
import requests
from user_sim.utils.url_management import get_content
from user_sim.utils.config import errors
import logging
from user_sim.utils.exceptions import *

logger = logging.getLogger('Info Logger')

###################################################
# THE CONNECTORS NEED HEAVY REFACTORING TO JUST
# ONE OR TWO CLASSES

# def get_get_content():
#     from user_sim.utils.url_management import get_content
#     return get_content
#
# get_content = get_get_content()

class Chatbot:
    def __init__(self, connector):
        self.fallback = 'I do not understand you'

        self.connector_args = connector
        self.config = self.connector_args.get("config")
        self.payload = self.connector_args.get("payload", {})

        self.api_url = self.config.get("api_url", "")
        self.headers = self.config.get("headers", {})
        self.timeout = self.config.get("timeout", 0)
        self.request_key = self.config.get("request_key", "")
        self.response_key = self.config.get("response_key", "")


    def execute_with_input(self, user_msg):
        """Returns a pair [bool, str] in which the first element is True if the chatbot returned normally,
           and the second is the message.
           Otherwise, False means that there is an error in the chatbot."""
        self.parse_message_to_payload(user_msg)

        response = requests.post(self.api_url, headers=self.headers, json=self.payload, timeout=self.timeout)

        try:
            if response.status_code == 200:
                response_json = response.json()
                # response_dict = json.loads(response.text)
                responses = response_json[self.response_key]
                if isinstance(responses, list):
                    all_responses = get_content('\n'.join(responses))
                else:
                    all_responses = get_content(responses)
                return True, all_responses
            else:
                # There is an error, but it is an internal error
                logger = logging.getLogger('Info Logger')
                logger.error(f"Server error {response.status_code}")
                errors.append({response.status_code: f"Couldn't get response from the server"})
                return False, f"Something went wrong. Status Code: {response.status_code}"

        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('Info Logger')
            logger.error(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'
        except requests.Timeout:
            logger = logging.getLogger('Info Logger')
            logger.error(f"No response was received from the server in less than {self.timeout}")
            errors.append({504: f"No response was received from the server in less than {self.timeout}"})
            return False, 'timeout'

    def parse_message_to_payload(self, message):

        def pmtp(rk):
            if "." in rk:
                keys = rk.split('.')
                ref = self.payload
                for key in keys[:-1]:
                    if key not in ref or not isinstance(ref[key], dict):
                        ref[key] = {}
                    ref = ref[key]
                ref[keys[-1]] = message
                self.payload = ref
            else:
                self.payload[rk] = message

        if isinstance(self.request_key, list):
            for rk in self.request_key:
                pmtp(rk)
        else:
            pmtp(self.request_key)

    def parse_keys(self, structure, message, msg_type):

        def pmtp(ks):
            if "." in ks:
                keys = ks.split('.')
                ref = structure
                for key in keys[:-1]:
                    if key not in ref or not isinstance(ref[key], dict):
                        ref[key] = {}
                    ref = ref[key]
                if msg_type == "payload":
                    ref[keys[-1]] = message
                    self.payload = ref
                elif msg_type == "response":
                    self.response_key = ref
            else:
                if msg_type == "payload":
                    self.payload[ks] = message

        if msg_type == "payload":
            key_strings = self.request_key
        elif msg_type == "response":
            key_strings = self.response_key
        else:
            raise "invalid message type."

        if isinstance(key_strings, list):
            for key_string in key_strings:
                pmtp(key_string)
        else:
            pmtp(key_strings)

    @staticmethod
    def get_connector_args(connector_path):
        if isinstance(connector_path, str):
            with open(connector_path, 'r', encoding='UTF-8') as f:
                connector_args = yaml.safe_load(f)
            return connector_args
        elif isinstance(connector_path, dict):
            return connector_path
        else:
            raise InvalidItemType("Connector item is not a string (path) or a dictionary (yaml content).")


##############################################################################################################
# RASA
class ChatbotRasa(Chatbot):
    def __init__(self, connector):
        Chatbot.__init__(self, connector)
        # self.connector_args = self.get_connector_args(connector)
        # self.api_url = self.connector_args["api_url"]
        self.id = None
        # self.api_url = self.config.get("api_url", "")


    def execute_with_input(self, user_msg):
        if self.id is None:
            self.id = str(uuid.uuid4())

        new_data = {
            "sender": self.id,
            "message": user_msg
        }
        post_response = requests.post(self.api_url, json=new_data)
        post_response_json = post_response.json()
        if len(post_response_json) > 0:
            message = '\n'.join([r.get('text') for r in post_response_json])
            return True, message
        else:
            return True, ''


##############################################################################################################
# 1million bot chatbots
class ChatbotMillionBot(Chatbot):
    def __init__(self, connector):
        Chatbot.__init__(self, connector)
        self.connector_args = self.get_connector_args(connector)
        self.headers = {}
        self.payload = {}
        self.api_url = ""
        self.id = None

        self.reset_url = None
        self.reset_payload = None

        self.init_chatbot(self.connector_args['payload'],
                          self.connector_args['timeout'])



    def init_chatbot(self, payload, timeout):
        first_api_url = "https://api.1millionbot.com/api/public/users"
        first_payload = payload
        first_header = {
            "Content-Type": "application/json",
            "Authorization": "API-KEY 60553d58c41f5dfa095b34b5"
        }
        first_response = requests.post(first_api_url, headers=first_header, json=first_payload, timeout=timeout)
        first_response = first_response.json()

        second_payload = {
            "bot": "60a3be81f9a6b98f7659a6f9",
            "user": first_response["user"]["_id"],
            "language": "es",
            "integration": "web",
            "gdpr": True
        }
        second_header = {
        "Content-Type": "application/json",
        "Authorization": "60a3bee2e3987316fed3218f"}
        second_api_url = "https://api.1millionbot.com/api/public/conversations"
        second_response = requests.post(second_api_url, headers=second_header, json=second_payload, timeout=timeout)
        second_response = second_response.json()

        third_payload = {
            "bot": "60a3be81f9a6b98f7659a6f9",
            "sender": first_response["user"]["_id"],
            "conversation": second_response["conversation"]["_id"],
            "sender_type": "User",
            "language": "es",
            "message": {
                "text": "con quien hablo?"
            }
        }
        third_api_url = "https://api.1millionbot.com/api/public/messages"
        self.api_url = third_api_url
        self.headers = second_header
        self.payload = third_payload
        self.timeout = timeout

        # Always generate a new ID for the conversation
        #import uuid
        #unique_id = uuid.uuid4()
        #conversation_id = unique_id.hex

        # Randomly replace a letter in the conversation_id with a hexadecimal digit
        #import random
        #import string
        #conversation_id = list(conversation_id)
        #conversation_id[random.randint(0, len(conversation_id)-1)] = random.choice(string.hexdigits)
        #conversation_id = ''.join(conversation_id)


        # self.reset_url = "https://api.1millionbot.com/api/public/live/status"
        # self.reset_payload = {"bot": bot_id,
        #                       "conversation": conversation_id,
        #                       "status": {
        #                           "origin": url,
        #                           "online": False,
        #                           "typing": False,
        #                           "deleted": True,
        #                           "attended": {},
        #                           "userName": "UAM/UMU"}
        #
        #                       }



    def execute_with_input(self, user_msg):

        self.payload['message']["text"] = user_msg
        timeout = self.timeout
        try:
            response = requests.post(self.api_url, headers=self.headers, json=self.payload, timeout=timeout)
            response_json = response.json()
            if response.status_code == 200:
                text_response = ""
                for answer in response_json['response']:
                    # to-do --> pass the buttons in the answer?
                    if 'text' in answer:
                        text_response += answer['text']+"\n"
                    elif 'payload' in answer:
                        text_response += f"\n\nAVAILABLE BUTTONS:\n\n"
                        if 'cards' in answer['payload']:
                            for card in answer['payload']['cards']:
                                if 'buttons' in card:
                                    text_response += self.__translate_buttons(card['buttons'])
                        elif 'buttons' in answer['payload']:
                            text_response += self.__translate_buttons(answer['payload']['buttons'])

                return True, text_response
            else:
                # There is an error, but it is an internal error
                print(f"Server error {response_json.get('error')}")
                errors.append({500: f"Couldn't get response from the server"})
                return False, response_json.get('error')
        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('my_app_logger')
            logger.error(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'
        except requests.Timeout:
            logger = logging.getLogger('my_app_logger')
            logger.error(f"No response was received from the server in less than {timeout}")
            errors.append({504: f"No response was received from the server in less than {timeout}"})
            return False, 'timeout'


    def __translate_buttons(self, buttons_list) -> str:
        text_response = ''
        for button in buttons_list:
            if 'text' in button:
                text_response += f"- BUTTON TEXT: {button['text']}"
            if 'value' in button:
                text_response += f" LINK: {button['value']}\n"
            else:
                text_response += f" LINK: <empty>\n"
        return text_response


class ChatbotTaskyto(Chatbot):
    def __init__(self, connector):
        Chatbot.__init__(self, connector)
        self.id = None
        self.connector_args = self.get_connector_args(connector)
        self.api_url = self.connector_args["config"]["api_url"]
        self.timeout = self.connector_args["config"]["timeout"]

    def execute_with_input(self, user_msg):
        if self.id is None:
            try:
                post_response = requests.post(self.api_url + '/conversation/new')
                post_response_json = post_response.json()
                self.id = post_response_json.get('id')
            except requests.exceptions.ConnectionError:
                logger.error(f"Couldn't connect with chatbot")
                errors.append({500: f"Couldn't connect with chatbot"})
                return False, 'cut connection'
            except Exception:
                logger.error(f"Server error: invalid payload")
                errors.append({post_response.status_code: f"Server error"})
                return False, 'chatbot server error'

        if self.id is not None:
            new_data = {
                "id": self.id,
                "message": user_msg
            }

            try:
                try:
                    post_response = requests.post(self.api_url + '/conversation/user_message', json=new_data, timeout=self.timeout)
                except requests.Timeout:
                    logger.error(f"No response was received from the server in less than {self.timeout}")
                    errors.append({504: f"No response was received from the server in less than {self.timeout}"})
                    return False, 'timeout'
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"Couldn't get response from the server: {e}")
                    errors.append({500: f"Couldn't get response from the server"})
                    return False, 'chatbot internal error'

                post_response_json = post_response.json()

                if post_response.status_code == 200:
                    assistant_message = post_response_json.get('message')
                    message = get_content(assistant_message) # get content process the message looking for images, pdf, or webpages
                    return True, message

                else:
                    # There is an error, but it is an internal error
                    errors.append({500: "Chatbot internal error"})
                    return False, post_response_json.get('error')
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"Couldn't get response from the server: {e}")
                errors.append({500: f"Couldn't get response from the server"})
                return False, 'chatbot internal error'

        return True, ''

    def execute_starter_chatbot(self):
        timeout = 20
        try:
            post_response = requests.post(self.api_url + '/conversation/new')
            post_response_json = post_response.json()
            self.id = post_response_json.get('id')
            if post_response.status_code == 200:
                assistant_message = post_response_json.get('message')
                message = get_content(assistant_message)
                if message is None:
                    return True, 'Hello'
                else:
                    return True, message
            else:
                # There is an error, but it is an internal error
                logger.error(f"Chatbot internal error")
                errors.append({500: "Chatbot internal error"})
                return False, post_response_json.get('error')
        except requests.exceptions.ConnectionError:
            logger.error(f"Couldn't connect with chatbot")
            errors.append({500: f"Couldn't connect with chatbot"})
            return False, 'cut connection'
        except requests.Timeout:
            logger.error(f"No response was received from the server in less than {timeout}")
            errors.append({504: f"No response was received from the server in less than {timeout}"})
            return False, 'timeout'


##############################################################################################################
# Serviceform
class ChatbotServiceform(Chatbot):
    def __init__(self, connector):
        Chatbot.__init__(self, connector)

        self.connector_args = self.get_connector_args(connector)

        self.api_url = self.connector_args["api_url"]
        self.headers = self.connector_args["headers"]
        self.payload = self.connector_args["payload"]
        self.timeout = self.connector_args["timeout"]

        # self.url = "https://dash.serviceform.com/api/ai"
        # self.headers = {
        #     'Content-Type': 'text/plain;charset=UTF-8'
        # }
        # self.payload = {"sid":"1729589460223tvzbcxe5zocgr5hs",
        #                 "tid":"haGDRXUPY9tQOsOS44jY",
        #                 "message":"Hello",
        #                 "extraTraining":"",
        #                 "assistant_id":"asst_PUNPPDAFOgHRLrlmHhDuQhCM"}

    def execute_with_input(self, user_msg):
        self.payload['message'] = user_msg

        try:
            response = requests.post(self.api_url, headers=self.headers, json=self.payload, timeout=self.timeout)
            if response.status_code == 200:
                data_bytes = response.content
                data_str = data_bytes.decode('utf-8')
                data_dict = json.loads(data_str)
                return True, data_dict['response']
            else:
                # There is an error, but it is an internal error
                print(f"Server error {response.status_code}")
                errors.append({response.status_code: f"Couldn't get response from the server"})
                return False, f"Something went wrong. Status Code: {response.status_code}"
        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('my_app_logger')
            logger.log(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'
        except requests.Timeout:
            logger = logging.getLogger('my_app_logger')
            logger.error(f"No response was received from the server in less than {self.timeout}")
            errors.append({504: f"No response was received from the server in less than {self.timeout}"})
            return False, 'timeout'



##############################################################################################################
# Kuki chatbot
# class KukiChatbot(Chatbot):
#     def __init__(self, connector):
#         Chatbot.__init__(self, connector)
#
#         self.connector_args = self.get_connector_args(connector)
#         self.api_url = self.connector_args["api_url"]
#         self.headers = self.connector_args["headers"]
#         self.payload = self.connector_args["payload"]
#         self.timeout = self.connector_args["timeout"]
#
#         # self.url = "https://kuli.kuki.ai/cptalk"
#         # self.headers = {
#         #     'Content-Type': 'application/x-www-form-urlencoded'  # Standard for form data
#         # }
#         # self.payload = {
#         #     'uid': 'da8bb9b3e54e9a4b',
#         #     'input': 'Hello',
#         #     'sessionid': '485255309'
#         # }
#
#     def execute_with_input(self, user_msg):
#         self.payload['input'] = user_msg
#
#         try:
#             response = requests.post(self.api_url, headers=self.headers, data=self.payload, timeout=self.timeout)
#             if response.status_code == 200:
#                 response_dict = json.loads(response.text)
#                 responses = response_dict['responses']
#                 all_responses = get_content('\n'.join(responses))
#                 return True, all_responses
#             else:
#                 # There is an error, but it is an internal error
#                 print(f"Server error {response.status_code}")
#                 errors.append({response.status_code: f"Couldn't get response from the server"})
#                 return False, f"Something went wrong. Status Code: {response.status_code}"
#         except requests.exceptions.JSONDecodeError as e:
#             logger = logging.getLogger('my_app_logger')
#             logger.log(f"Couldn't get response from the server: {e}")
#             return False, 'chatbot internal error'
#         except requests.Timeout:
#             logger = logging.getLogger('my_app_logger')
#             logger.error(f"No response was received from the server in less than {self.timeout}")
#             errors.append({504: f"No response was received from the server in less than {self.timeout}"})
#             return False, 'timeout'
#
#
# ##############################################################################################################
# # Julie chatbot
# class JulieChatbot(Chatbot):
#     def __init__(self, connector):
#         Chatbot.__init__(self, connector)
#
#         self.connector_args = self.get_connector_args(connector)
#         self.api_url = self.connector_args["api_url"]
#         self.headers = self.connector_args["headers"]
#         self.payload = self.connector_args["payload"]
#         self.timeout = self.connector_args["timeout"]
#
#         # self.url = 'https://askjulie2.nextit.com/AlmeAPI/api/Conversation/Converse'
#         # self.headers = {
#         #     'Content-Type': 'application/json',
#         # }
#         # self.payload = {"userId":"4b62a896-85f0-45dd-b94c-a6496f831107",
#         #    "sessionId":"724e371e-9917-4ab2-9da4-6809199366eb",
#         #    "question":"How are you?",
#         #    "origin":"Typed",
#         #    "displayText":"How are you?",
#         #    "parameters":{
#         #        "Context":{
#         #            "CurrentUrl":
#         #                {
#         #                    "AbsolutePath":"https://www.amtrak.com/home.html",
#         #                    "Protocol":"https:",
#         #                    "Host":"www.amtrak.com",
#         #                    "HostName":"www.amtrak.com",
#         #                    "Port":"",
#         #                    "Uri":"/home.html",
#         #                    "Query":"",
#         #                    "Fragment":"",
#         #                    "Origin":"https://www.amtrak.com",
#         #                    "Type":"embedded",
#         #                    "PageName":"Amtrak Tickets, Schedules and Train Routes"
#         #                }
#         #         },
#         #        "UiVersion":"1.33.17"
#         #    },
#         #    "channel":"Web",
#         #    "language":"en-US",
#         #    "accessKey":"00000000-0000-0000-0000-000000000000"
#         # }
#
#     def execute_with_input(self, user_msg):
#         self.payload['question'] = user_msg
#         self.payload['displayText'] = user_msg
#
#         try:
#             response = requests.post(self.url, headers=self.headers, json=self.payload, timeout=self.timeout)
#             if response.status_code == 200:
#                 response_dict = json.loads(response.text)
#                 chat_response = response_dict['text']
#                 if 'displayLinkCollection' in response_dict and response_dict['displayLinkCollection']:
#                     buttons = self.__translate_buttons(response_dict['displayLinkCollection'])
#                     chat_response += f"\n\n{buttons}"
#                 return True, chat_response
#             else:
#                 # There is an error, but it is an internal error
#                 print(f"Server error {response.status_code}")
#                 errors.append({response.status_code: f"Couldn't get response from the server"})
#                 return False, f"Something went wrong. Status Code: {response.status_code}"
#         except requests.exceptions.JSONDecodeError as e:
#             logger = logging.getLogger('my_app_logger')
#             logger.log(f"Couldn't get response from the server: {e}")
#             return False, 'chatbot internal error'
#         except requests.Timeout:
#             logger = logging.getLogger('my_app_logger')
#             logger.error(f"No response was received from the server in less than {self.timeout}")
#             errors.append({504: f"No response was received from the server in less than {self.timeout}"})
#             return False, 'timeout'
#
#     def __translate_buttons(self, buttons_dict) -> str:
#         button_description = 'AVAILABLE BUTTONS: '
#         for section in buttons_dict['Sections']:
#             for button in section["Links"]:
#                 button_text = ""
#                 if 'DisplayText' in button:
#                     button_text += f"- BUTTON TEXT: {button['DisplayText']}"
#                 if 'Metadata' in button and 'UnitUID' in button['Metadata']:
#                     button_text += f" LINK: {button['Metadata']['UnitUID']}\n"
#                 else:
#                     button_text += f" LINK: <empty>\n"
#                 button_description += f'\n {button_text}'
#         return button_description
