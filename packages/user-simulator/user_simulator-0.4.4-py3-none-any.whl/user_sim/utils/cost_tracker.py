import os
import csv
import pandas as pd
import tiktoken
from user_sim.utils.exceptions import *
from user_sim.utils import config
from datetime import datetime
from typing import List, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult, ChatGeneration, ChatResult
from langchain.chat_models import ChatModel
import logging

logger = logging.getLogger('Info Logger')

cost_rates = {
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.0020},
    "gpt-4":         {"prompt": 0.03,   "completion": 0.06},
    # later, if you try e.g. Anthropic:
    "claude-v1":     {"prompt": 0.0075, "completion": 0.015},
}

columns = ["Conversation",
           "Test Name",
           "Module",
           "Model",
           "Total Cost",
           "Timestamp",
           "Input Cost",
           "Input Message",
           "Output Cost",
           "Output Message"]


def create_cost_dataset(serial, test_cases_folder):
    folder = f"{test_cases_folder}/reports/__cost_reports__"
    file = f"cost_report_{serial}.csv"

    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created cost report folder at: {folder}")

    path = f"{folder}/{file}"
    if not os.path.exists(path):
        cost_df = pd.DataFrame(columns=columns)
        cost_df.to_csv(path, index=False)
        config.cost_ds_path = path
        logger.info(f"Cost dataframe created at {path}.")

    return path


def count_message_tokens(messages: List[dict], model_name: str) -> int:
    # """Rough token count for a list of role/content dicts via tiktoken."""
    # enc = tiktoken.encoding_for_model(model_name)
    # total = 0
    # for msg in messages:
    #     # include role token + content tokens
    #     total += len(enc.encode(msg["role"]))
    #     total += len(enc.encode(msg["content"]))
    # return total
    pass


class CostTrackingCallback(BaseCallbackHandler):
    """
    A LangChain callback that, on each LLM invocation,
      1. extracts token usage
      2. computes cost via a per-model rate table
      3. appends a row into a CSV in real time
    """
    def __init__(self):
        """
        csv_path: where to store the cost log
        cost_rates: {
          "<model_name>": {"prompt": <$/1K tokens>, "completion": <$/1K tokens>},
          ...
        }
        """
        path = create_cost_dataset(config.serial, )
        self.serial = config.serial
        self.csv_path = path
        self.cost_rates = cost_rates

        # If first time, write header
        # if not os.path.exists(self.csv_path):
        #     with open(self.csv_path, 'w', newline='') as f:
        #         writer = csv.writer(f)
        #         writer.writerow([
        #             "timestamp",
        #             "model_name",
        #             "prompt_tokens",
        #             "completion_tokens",
        #             "total_tokens",
        #             "total_cost_usd",
        #         ])

    def on_llm_end(self, result: LLMResult, **kwargs) -> None:
        # 1. pull out usage (providers like OpenAI put it in result.llm_output["usage"])
        usage = result.llm_output.get("usage", {})
        p_tokens = usage.get("prompt_tokens", 0)
        c_tokens = usage.get("completion_tokens", 0)
        total = usage.get("total_tokens", p_tokens + c_tokens)

        # 2. determine model name key
        model_name = (
            result.llm_output.get("model_name")
            or getattr(result, "model_name", None)
            or "unknown"
        )

        # 3. look up rates (per 1K tokens) and compute
        rates = self.cost_rates.get(model_name, {})
        cost = (p_tokens / 1000) * rates.get("prompt", 0.0) \
             + (c_tokens / 1000) * rates.get("completion", 0.0)

        # 4. append to CSV (real‐time)
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(),
                model_name,
                p_tokens,
                c_tokens,
                total,
                f"{cost:.8f}",
            ])

    def budgeted_invoke(
        self,
        llm: ChatModel,
        messages: List[dict],
        **invoke_kwargs
    ) -> ChatResult:
        """
        Checks your budget, then either:
          • returns "" if spent up
          • calls llm.invoke with max_tokens clipped to budget
        """
        model_name = llm.client.model_name  # or however your ChatModel exposes it
        max_toks = self.get_max_completion_tokens(messages, model_name)

        if max_toks is None:
            # unknown model: just invoke normally
            return llm.invoke(messages, callbacks=[self], **invoke_kwargs)

        if max_toks <= 0:
            # out of money
            raise BudgetExceeded(f"No budget remaining for model {model_name}")

        # enforce our budget
        invoke_kwargs.setdefault("config", {})
        invoke_kwargs["config"]["max_tokens"] = max_toks

        return llm.invoke(messages, callbacks=[self], **invoke_kwargs)