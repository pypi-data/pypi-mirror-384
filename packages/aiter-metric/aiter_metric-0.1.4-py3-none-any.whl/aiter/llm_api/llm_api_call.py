from ..llm_api.googleai_api import create_googleai_client, call_googleai_api
from ..llm_api.mistral_api import create_mistral_client, call_mistral_api
from ..config import MODELS_CONFIG

API_CLIENTS = {
    "gemini": create_googleai_client,
    "mistral": create_mistral_client
}

API_CALLS = {
    "gemini": call_googleai_api,
    "mistral": call_mistral_api
}

def create_client(model, api_key):
    api_name = MODELS_CONFIG[model]["api"]
    return API_CLIENTS[api_name](api_key)


def call_api(client, prompt, model, **kwargs):
    model_config = MODELS_CONFIG[model]
    api_name = model_config["api"]
    return API_CALLS[api_name](client, prompt, model_config, **kwargs)