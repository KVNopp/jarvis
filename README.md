# Omega

## Celular (Termux)

Veja [GUIA-CELULAR.md](GUIA-CELULAR.md) para instalar o Omega no celular, direto do GitHub.
Após a instalação, use `omega ligar pc`, `omega desligar pc` ou `omega` para conversar.
No chat, `/ligar`, `/desligar`, `Omega, liga o PC` e `Omega, desliga o PC` usam
Wake-on-LAN e SSH diretamente, sem passar pelo Ollama. O desligamento é imediato.
Os dados do PC podem ser ajustados com as variáveis `PC_*` descritas no guia.
O terminal no Android usa `requirements-termux.txt`; interface e voz do Windows
continuam no PC. A conversa livre depende do Ollama, conectado por túnel SSH.

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

## LIFE OS (tarefas e hábitos)

O Omega lê e grava direto no [LIFE OS](https://github.com/KVNopp/life-os), pelo mesmo Supabase.
O que ele cria aparece no app do PC e do celular em segundos.

Configurar (uma vez):

1. No `.env`, preencha `LIFEOS_SUPABASE_URL` e `LIFEOS_SUPABASE_KEY` com os mesmos valores de
   **LIFE OS → Ajustes → Projeto Supabase** (a chave pública *anon*, nunca a *service_role*).
2. No terminal: `python main.py /lifeos entrar` e digite o e-mail e a senha da sua conta do LIFE OS.
   A senha não é salva: o Omega guarda só o token da sessão em `lifeos_sessao.json`, que é renovado
   sozinho e ignorado pelo Git. `/lifeos sair` apaga essa sessão.

Usar (no terminal, na interface ou no Termux; não precisa do Ollama):

| Comando | Frase equivalente |
|---|---|
| `/hoje` | "o que eu tenho pra hoje?", "como está meu dia?" |
| `/tarefas` | "quais são minhas tarefas" |
| `/tarefa Estudar física amanhã` | "cria a tarefa estudar física pra amanhã" |
| `/feito Estudar física` | "terminei a tarefa estudar física" |
| `/habito Leitura` | "marquei o hábito de leitura" |

O prazo da tarefa é opcional: `hoje`, `amanhã`, `depois de amanhã`, `05/12` ou `05/12/2027`.
Para concluir tarefas e marcar hábitos basta parte do nome; se houver mais de um parecido,
o Omega lista as opções. Se o mesmo item for editado no app ao mesmo tempo, vale a regra do
LIFE OS: vence a edição mais recente, e o Omega avisa para tentar de novo.

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
https://pypi.org/project/ddgs/ e https://openweathermap.org/current.

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

## Abrir aplicativos

Na interface ou no terminal, diga `abra a calculadora`, `abra o Chrome` ou use
`/abrir vscode`. `/apps` mostra os aplicativos cadastrados. A ação funciona sem Ollama.

Suporte inicial: Calculadora, Bloco de Notas, Paint, Explorador de Arquivos, Chrome,
Edge, VS Code e Spotify. O aplicativo precisa estar instalado em um dos caminhos
conhecidos de `computer.py`; instalações personalizadas e algumas versões da Store
podem não ser encontradas. Novos aplicativos podem ser cadastrados no dicionário `APPS`.

A abertura usa executáveis cadastrados, sem shell nem argumentos livres. O Omega
informa que solicitou a abertura ao Windows; não verifica o conteúdo da janela.
Esta versão abre aplicativos, mas ainda não clica, digita ou controla suas janelas.

## Chat e voz

Instale `python -m pip install -r requirements-voice.txt` e abra `python interface.py`.
Selecione **Chat** para digitar, ou **Voz** para habilitar **Falar** e ouvir as respostas.
O botão Falar captura oito segundos pelo microfone padrão. A transcrição aparece no campo:
revise e clique em Enviar. Isso também evita executar pedidos de aplicativos por engano.
**Parar voz** interrompe a leitura; voltar para Chat também silencia o Omega.

O reconhecimento envia áudio ao Google via SpeechRecognition, exige internet e pede
consentimento na primeira captura de cada sessão. O áudio não é salvo pelo Omega.
A leitura é local via pyttsx3 e usa uma voz portuguesa do Windows quando instalada.
O chat continua funcionando sem as dependências opcionais de voz.
Referências: https://pypi.org/project/SpeechRecognition/ e https://pypi.org/project/pyttsx3/.

### Voz neural

No seletor **Voz do Omega**, escolha **oproprio** ou **daydiva** e use **Testar voz**.
oproprio usa ritmo levemente mais lento e tom um pouco mais grave. As duas opções
usam síntese neural online via edge-tts (serviço Microsoft Edge); o texto da resposta
é enviado ao serviço após consentimento na interface. O áudio fica em memória.
**Windows (offline)** mantém a síntese local. A seleção vale para a sessão atual.
Referência: https://github.com/rany2/edge-tts.
