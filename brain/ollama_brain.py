import ollama

def perguntar(mensagem):
    try:
        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'system',
                'content': 'Você é Jarvis, um assistente pessoal inteligente, educado e eficiente. Responda de forma concisa e prestativa.',
            },
            {
                'role': 'user',
                'content': mensagem,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"Erro ao conectar com o Ollama: {str(e)}\nCertifique-se de que o Ollama está rodando e que você baixou o modelo (ollama run llama3)."
