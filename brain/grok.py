import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system

load_dotenv()

client = Client(
    api_key=os.getenv("XAI_API_KEY")
)

chat = client.chat.create(
    model="grok-4.6",
    messages=[
        system("Você é Jarvis, um assistente pessoal inteligente.")
    ]
)

def perguntar(mensagem):
    chat.append(user(mensagem))
    response = chat.sample()
    return response.content
# um dia eu volto para adicionar o grok com um sistema de memória, mas por enquanto vou deixar ele desativado, pois nao tenho grana!