# Omega

Assistente pessoal no terminal, sem login, com Ollama, memória persistente, clima e pesquisa web.

## Executar

```powershell
python -m pip install -r requirements.txt
python main.py
```

O Ollama deve estar em execução e ter o modelo `llama3` instalado (`ollama pull llama3`).
É possível mudar `OLLAMA_MODEL` e `OLLAMA_HOST` no `.env`. Use `.env.example` como referência,
sem sobrescrever suas configurações existentes. O clima usa `OPENWEATHER_API_KEY`.

## Uso

Converse normalmente ou use `/ajuda`, `/hora`, `/data`, `/clima São Paulo`,
`/buscar assunto`, `/memoria` e `/sair`. Ctrl+C também encerra.
Hora e data por comando funcionam mesmo com o Ollama desligado.

## Memória

O arquivo `memoria.json` original continua sendo utilizado, sempre relativo à pasta do projeto.
A reforma preserva uma cópia em `memoria.pre-reforma.json`. Cada gravação usa um arquivo temporário
seguido de substituição, guardando a versão anterior em `memoria.json.bak`.
Um JSON inválido interrompe a inicialização sem apagar o arquivo. Para recuperar, feche o programa,
confira o backup e copie-o para `memoria.json`.

O histórico completo permanece no disco. Para controlar o tamanho enviado ao modelo, a conversa usa
mensagens recentes e até quatro trechos antigos selecionados por palavras-chave. Essa recuperação
é simples e não garante lembrar todos os detalhes. O prompt de sistema atual substitui, apenas no
contexto enviado, o prompt antigo; o registro original permanece no arquivo.
Erros de integração não são gravados como respostas. Execute somente uma instância por arquivo de memória.

A memória é pessoal: `memoria.json` e seus backups ficam apenas no computador e são ignorados pelo Git.
Versões já presentes em commits antigos continuam no histórico do repositório.
Não publique o histórico ou o `.env`. A chave de clima antes embutida no código
foi movida para o `.env`; substitua essa chave no provedor caso ela tenha sido compartilhada.

## Verificação

```powershell
python -m unittest discover -s tests -v
```

Os testes usam arquivos temporários e serviços simulados, sem modificar sua memória real.

Referências das integrações: https://github.com/ollama/ollama-python,
https://pypi.org/project/duckduckgo-search/ e https://openweathermap.org/current.

## Origem e histórico do projeto

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

## Interface gráfica

```powershell
python interface.py
```

A janela usa Tkinter (incluído na instalação padrão do Python para Windows), tema escuro,
atalhos, texto selecionável e as 60 mensagens mais recentes. Enter envia; Shift+Enter cria uma nova linha.
A IA trabalha em segundo plano. O clima solicita a cidade em uma janela quando necessário.
A interface compartilha a memória com o terminal: use apenas um deles por vez.
O terminal continua disponível com `python main.py`.
