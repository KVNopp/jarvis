Esse sera meu primeiro agente usando de Inteligencia Artificial. Usando em maioria a linguagem python, farei um agente que me atenda e me ajude a desenvolver minhas habilidades com a logica da programaçao e aprender sobre as linguagens!
 📝 Nota de Atualização: Implementação de Roteamento Inteligente 05/09/2026 - 17:52

  O que foi mudado:
  1. Fim das Palavras-Chave: Removi aquela lista gigante de palavras (search_keywords) do main.py. O Omega não precisa mais que você diga "pesquise" ou "notícia" para usar a internet.
  2. Criação do "Roteador de Intenções": Adicionei a função classificar_intencao no arquivo ollama_brain.py. Agora, antes de cada resposta, o Omega faz uma análise rápida e decide sozinho se a pergunta pede:
     - HORA $\rightarrow$ Chama a função de hora.
     - DATA $\rightarrow$ Chama a função de data.
     - CLIMA $\rightarrow$ Pergunta a cidade e busca o clima.
     - WEB $\rightarrow$ Otimiza a busca, pesquisa no DuckDuckGo e processa a resposta.
     - CONVERSA $\rightarrow$ Responde normalmente usando o conhecimento interno.
  3. Otimização da Memória: Organizei a forma como o Omega salva a memória no main.py para evitar que o código ficasse repetitivo e lento.
