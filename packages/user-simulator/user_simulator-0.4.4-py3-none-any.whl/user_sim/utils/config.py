# execution data
errors = []
conversation_name = ""
serial = ""
# model = "gpt-4o-mini"
cost_ds_path = None
test_name = ''
ignore_cache = False
update_cache = False
clean_cache = False


# project data
root_path = ""
project_folder_path = ""
src_path = ""
#data
cache_path = ""
pdfs_path = ""
audio_files_path = ""
#custom
profiles_path = ""
custom_personalities_path = ""
custom_types_path = ""
test_cases_folder = ""
types_dict = {}
#default
default_types_path = ""
default_personalities_path = ""


# cost metrics
token_count_enabled = True
limit_cost = 10000000000
limit_individual_cost = 10000000000
total_cost = 0
total_individual_cost = 0

#llm
model = "gpt-4o-mini"
model_provider = "openai"


# context
default_context = [
    "You are a helpful user simulator that test chatbots.",
    "Don't add starting sentences, for example 'Okay, here we go'. The first thing you say must be already in the role of a user"
    "You must act like a user since the beginning of the conversation. "
    "never recreate a whole conversation, just act like you're a user or client",
    "never generate a message starting by 'user:'",
    'Sometimes, interact with what the assistant just said.',
    'Never act as the assistant, always behave as a user.',
    "Don't end the conversation until you've asked everything you need.",
    "you're testing a chatbot, so there can be random values or irrational things "
    "in your requests"
]