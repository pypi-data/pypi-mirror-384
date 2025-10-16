import os
import csv
import pandas as pd
from datetime import datetime
from typing import List, Union
import tiktoken

from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult, ChatGeneration, ChatResult
from user_sim.utils import config
import logging

logger = logging.getLogger('Info Logger')

cost_rates = {
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.0020},
    "gpt-4":         {"prompt": 0.03,   "completion": 0.06},
    "gpt-4o-mini":   {"prompt": 0.03,   "completion": 0.06},
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

    if config.cost_ds_path is None:
        folder = f"{test_cases_folder}/reports/__cost_reports__"
        file = f"cost_report_{serial}.csv"
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created cost report folder at: {folder}")

        path = f"{folder}/{file}"

        cost_df = pd.DataFrame(columns=columns)
        cost_df.to_csv(path, index=False)
        config.cost_ds_path = path
        logger.info(f"Cost dataframe created at {path}.")
        return path
    else:
        return config.cost_ds_path



class BudgetExceeded(Exception):
    """Raised when there's no budget left for a new LLM call."""
    pass

def count_message_tokens(messages: List[dict], model_name: str) -> int:
    """Rough token count for a list of role/content dicts via tiktoken."""
    enc = tiktoken.encoding_for_model(model_name)
    total = 0
    for msg in messages:
        # include role token + content tokens
        total += len(enc.encode(msg["role"]))
        total += len(enc.encode(msg["content"]))
    return total

class CostTrackingCallback(BaseCallbackHandler):
    """
    1. Logs every call’s token usage and cost to CSV.
    2. Tracks cumulative spend against a total budget.
    3. Provides a `budgeted_invoke` helper to enforce the budget.
    """

    def __init__(
        self,
        # csv_path: str,
        # cost_rates: dict,
        # total_budget_usd: float
    ):
        """
        csv_path:        path to your log CSV
        cost_rates:      {"model": {"prompt": $/1K, "completion": $/1K}, …}
        total_budget_usd: how many dollars you're willing to spend in total
        """
        path = create_cost_dataset(config.serial, config.test_cases_folder)
        self.serial = config.serial
        self.csv_path = path
        self.cost_rates = cost_rates
        self.total_budget = 5
        self.spent = 0.0


        # self.csv_path = csv_path
        # self.cost_rates = cost_rates
        # self.total_budget = total_budget_usd
        # self.spent = 0.0

        # write header if new
        # if not os.path.exists(self.csv_path):
        #     with open(self.csv_path, "w", newline="") as f:
        #         w = csv.writer(f)
        #         w.writerow([
        #             "timestamp","model_name",
        #             "prompt_tokens","completion_tokens","total_tokens",
        #             "call_cost_usd","cumulative_spent_usd"
        #         ])

    def on_llm_end(self, result: LLMResult, **kwargs) -> None:
        # pull OpenAI‐style usage
        usage = result.llm_output.get("usage", {})
        p = usage.get("prompt_tokens", 0)
        c = usage.get("completion_tokens", 0)
        tot = usage.get("total_tokens", p + c)

        # model lookup
        model = result.llm_output.get("model_name") or getattr(result, "model_name", "unknown")
        rates = self.cost_rates.get(model, {"prompt":0.0,"completion":0.0})
        cost = (p/1000)*rates["prompt"] + (c/1000)*rates["completion"]

        # update spend
        self.spent += cost
        print(self.spent)
        # append row
        with open(self.csv_path, "a", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                datetime.utcnow().isoformat(),
                model, p, c, tot,
                f"{cost:.8f}",
                f"{self.spent:.8f}"
            ])

    def get_max_completion_tokens(self,
                                  messages: List[dict],
                                  model_name: str
                                 ) -> Union[int, None]:
        """
        Based on your remaining budget, estimate how many completion tokens you can afford.
        Returns None if model not in cost_rates.
        """
        if model_name not in self.cost_rates:
            return None

        rates = self.cost_rates[model_name]
        # 1. count prompt tokens, cost them
        p_tokens = count_message_tokens(messages, model_name)
        cost_prompt = (p_tokens/1000) * rates["prompt"]
        remaining = self.total_budget - self.spent - cost_prompt

        # 2. if no budget left, signal
        if remaining <= 0:
            return 0

        # 3. convert back into max tokens for completion
        return int((remaining * 1000) / rates["completion"])



def budgeted_invoke(
    llm,
    callbacks,
    **invoke_kwargs
) -> ChatResult:
    """
    Checks your budget, then either:
      • returns "" if spent up
      • calls llm.invoke with max_tokens clipped to budget
    """


    model_name = llm.model_name  # or however your ChatModel exposes it
    max_toks = self.get_max_completion_tokens(messages, model_name)

    invoke_kwargs.setdefault("config", {})
    invoke_kwargs["config"].update({
        "max_tokens": max_toks,
        "callbacks": [self],  # ← put it here
    })
    if max_toks is None:
        # unknown model: just invoke normally
        return llm.invoke(messages, **invoke_kwargs)

    if max_toks <= 0:
        # out of money
        raise BudgetExceeded(f"No budget remaining for model {model_name}")

    # enforce our budget
    invoke_kwargs.setdefault("config", {})
    invoke_kwargs["config"]["max_tokens"] = max_toks

    return llm.invoke(messages, callbacks=[self], **invoke_kwargs)
