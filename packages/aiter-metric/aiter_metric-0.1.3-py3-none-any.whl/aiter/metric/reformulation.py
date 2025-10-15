from ..llm_api.llm_api_call import create_client, call_api
from ..utils import load_prompt
import pandas as pd
from tqdm import tqdm
from ..config import PROMPTS, PROMPTS_DIR, MODELS_CONFIG

class Request:
    def __init__(self, req: str = "", ref: str = "", con: str = ""):
        self.req = req
        self.ref = ref
        self.con = con 

    @classmethod
    def from_series(cls, row: pd.Series):
        return cls(
            req=row.get("request", ""),
            ref=row.get("reference", ""),
            con=row.get("context", ""),
        )

def format_prompt(base_prompt: str, request: Request, hypothesis: str) -> str:
    return base_prompt.format(
        req=request.req,
        ref=request.ref,
        con=request.con,
        hyp=hypothesis
        )

def reformulate(client, base_prompt: str, reformulation_model: str, request: Request, hypothesis: str) -> str:
    prompt = format_prompt(base_prompt, request, hypothesis)
    return call_api(client, prompt, model=reformulation_model)

def create_reformulations(df, version, api_key):
    reformulation_model = version["REFORMULATION_MODEL"]
    code_version = version["CODE_VERSION"]
    lang = version["LANG"]
    base_prompts = [load_prompt(code_version, lang, prompt_basepath) for prompt_basepath in PROMPTS[code_version]["paths"]]
    steps = PROMPTS[code_version]["steps"]
    client = create_client(reformulation_model, api_key)
    for idx in tqdm(df.index, desc="Reformulation"):
        request = Request.from_series(df.loc[idx])
        hypothesis = df.loc[idx, 'hypothesis']
        for i in range(len(steps)):
            hypothesis = reformulate(client, base_prompts[i], reformulation_model, request, hypothesis)
            df.at[idx, steps[i]] = hypothesis
    return df