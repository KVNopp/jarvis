import ollama

def perguntar(mensagem, historico):
    try:
        # A função agora é simples: ela recebe o histórico completo
        # (sistema + conversas anteriores + pergunta atual) e envia para o Ollama.
        response = ollama.chat(model='llama3', messages=historico)
        return response['message']['content']
    except Exception as e:
        return f"Erro ao conectar com o Ollama: {str(e)}\nCertifique-se de que o Ollama está rodando e que você baixou o modelo (ollama run llama3)."
