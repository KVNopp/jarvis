# Omega no celular (Termux)

Instalação do zero num celular Android. O código vem direto do GitHub, então não precisa copiar
arquivos do PC. Leva uns 10 minutos.

## 1. Instalar o Termux

Instale o **Termux** pelo [F-Droid](https://f-droid.org/packages/com.termux/) ou pela
[página de releases do GitHub](https://github.com/termux/termux-app/releases). A versão da
Play Store também funciona, mas costuma ficar para trás nas atualizações.

## 2. Baixar e instalar o Omega

No Termux, um comando por vez:

```bash
pkg update -y
pkg install git -y
git clone https://github.com/KVNopp/jarvis.git ~/omega
bash ~/omega/instalar-termux.sh
```

O instalador coloca o Python, o SSH e as dependências, cria o `.env` a partir do `.env.example`
e cria o comando `omega`, que funciona de qualquer pasta.

## 3. Conectar ao LIFE OS

Abra o `.env` e preencha as duas linhas do LIFE OS com os mesmos valores de
**LIFE OS → Ajustes → Projeto Supabase**:

```bash
nano ~/omega/.env
```

No nano, Ctrl+O salva e Ctrl+X sai. Depois:

```bash
omega /lifeos entrar
omega /hoje
```

A senha não é salva no celular, só o token da sessão.

| Comando | Faz |
|---|---|
| `omega /hoje` | tarefas e hábitos de hoje |
| `omega /tarefas` | lista as tarefas abertas |
| `omega /tarefa Estudar física amanhã` | cria a tarefa |
| `omega /feito Estudar física` | conclui a tarefa |
| `omega /habito Leitura` | marca o hábito hoje |
| `omega` | conversa (veja o item 5) |

Tudo aparece no app LIFE OS do celular e do PC em segundos.

## 4. Atualizar

Quando houver mudanças no GitHub:

```bash
omega atualizar
```

Ele baixa a versão nova e reinstala, sem mexer no seu `.env` nem na memória.

## 5. Ligar e desligar o PC (opcional)

Funciona só com o celular e o PC na **mesma rede Wi-Fi**. Os dados do PC (MAC, IP e usuário) já
vêm configurados; se o IP do PC mudar, ajuste `PC_IP` no `.env` ou reserve o IP no roteador.

**Ligar** (Wake-on-LAN) não precisa de nada extra: `omega ligar pc`.

**Desligar** usa SSH com uma chave própria deste celular. A chave do celular antigo não vem junto.

No celular:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/pc_controle -N "" -C celular-omega
termux-setup-storage
cp ~/.ssh/pc_controle.pub ~/storage/downloads/
```

Envie o arquivo `pc_controle.pub` da pasta Downloads para o PC (Quick Share, cabo USB ou
e-mail para você mesmo). É a parte **pública** da chave, pode ser enviada sem risco.
A parte privada (`pc_controle`, sem `.pub`) nunca sai do celular.

No PC, abra o **PowerShell como administrador** e rode (ajuste o caminho se o arquivo não estiver
em Downloads):

```powershell
Get-Content "$env:USERPROFILE\Downloads\pc_controle.pub" | Add-Content C:\ProgramData\ssh\administrators_authorized_keys
```

Teste no celular: `omega desligar pc`. O desligamento é imediato: salve seus arquivos antes.
Se o celular antigo não for mais usado, apague a linha dele em `administrators_authorized_keys`.

## 6. Conversa livre com a IA (opcional)

Comandos do LIFE OS, hora, data e ligar o PC funcionam sem IA. A conversa livre usa o Ollama do PC
por um túnel SSH (precisa da chave do item 5 e do PC ligado com o Ollama aberto):

```bash
ssh -f -N -i ~/.ssh/pc_controle \
  -o IdentitiesOnly=yes -o BatchMode=yes \
  -o ConnectTimeout=10 -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=2 \
  -L 127.0.0.1:11434:127.0.0.1:11434 \
  -l 'kvn-opp\keven' 192.168.15.2
omega
```

O túnel não expõe a porta do Ollama na rede. Reabra depois de reiniciar o PC ou perder a conexão.
Clima precisa de `OPENWEATHER_API_KEY` no `.env`. A pesquisa web usa o pacote opcional `ddgs`
(`pip install ddgs`), não testado no Termux.

## Observações

- A memória de conversa (`memoria.json`) do celular é separada da do PC. Tarefas e hábitos não:
  esses ficam no LIFE OS e são os mesmos nos dois.
- O Omega no celular funciona pelo terminal; a janela gráfica e a voz continuam só no PC.
- Os testes automáticos simulam o Supabase, o SSH e o Wake-on-LAN. A instalação real no
  celular precisa ser conferida no aparelho.
