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
