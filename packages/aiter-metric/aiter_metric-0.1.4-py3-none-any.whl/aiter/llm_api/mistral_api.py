import time
from mistralai import Mistral

def create_mistral_client(api_key):
    return Mistral(api_key=api_key)

def call_mistral_api(client, prompt, model_config, temperature=0.0, call_delay=False, retry_delay=False, max_retries=3):
    if not call_delay:
        call_delay = model_config['call_delay']
    if not retry_delay:
        retry_delay = model_config['retry_delay']
    model = model_config['name']
    retries = 0
    while retries < max_retries:
        try:
            chat_response = client.chat.complete(
                model=model,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
            )
            time.sleep(call_delay)
            return chat_response.choices[0].message.content

        except AttributeError as e:
            print(f"Erreur d'attribut : {e}")
            return 

        except Exception as e:
            print(f"Une erreur est survenue : {e}")
            retries += 1
            if retries >= max_retries:
                print(f"Erreur après {max_retries} tentatives : {e}")
                return None
            print(f"Nouvelle tentative ({retries}/{max_retries}) dans {retry_delay} secondes...")
            time.sleep(retry_delay)

        