# Omega no Moto G31 (Termux da Play Store)

## Instalar

Transfira `omega-g31.zip` para a pasta Downloads do celular. No Termux:

```bash
termux-setup-storage
pkg install unzip -y
mkdir -p ~/omega-g31
unzip -n ~/storage/downloads/omega-g31.zip -d ~/omega-g31
cd ~/omega-g31/omega
bash instalar-termux.sh
```

A extração com `-n` preserva arquivos existentes. Para uma atualização, extraia em uma nova pasta e execute o instalador dessa pasta.

## Um comando por ação

```bash
omega ligar pc
omega desligar pc
```

Também aceita `omega /ligar` e `omega /desligar`. Para conversar no terminal, execute `omega`; dentro dele, escreva `Omega, liga o PC` ou `Omega, desliga o PC`.

O desligamento é imediato, sem forçar o fechamento dos aplicativos. Salve seus documentos antes. O sinal de ligar é enviado por Wake-on-LAN; a resposta não confirma que o Windows terminou de iniciar.

Usa a configuração já testada: MAC `74:56:3C:B4:0C:65`, broadcast `192.168.15.255`, IP `192.168.15.2`, usuário `kvn-opp\keven` e chave `~/.ssh/pc_controle`. A chave permanece no celular. Os scripts e widgets anteriores continuam funcionando.

Celular e PC precisam estar na mesma rede local. Se o IP do PC mudar, ajuste `PC_IP` ou reserve o IP no roteador. As variáveis `PC_MAC`, `PC_BROADCAST`, `PC_IP`, `PC_USER` e `PC_SSH_KEY` podem ser configuradas no `.env` da pasta do Omega. Nenhuma senha está embutida.

## Conversa com IA

Ligar e desligar funcionam sem Ollama. A conversa livre ainda depende do Ollama do PC; esta versão não instala um modelo no G31.

Com o PC ligado e o Ollama em execução, abra um túnel no Termux:

```bash
ssh -f -N -i ~/.ssh/pc_controle \
  -o IdentitiesOnly=yes -o BatchMode=yes \
  -o ConnectTimeout=10 -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=2 \
  -L 127.0.0.1:11434:127.0.0.1:11434 \
  -l 'kvn-opp\keven' 192.168.15.2
omega
```

O túnel conecta o Omega do celular ao Ollama do PC sem expor a porta do Ollama na rede. Reabra o túnel depois de reiniciar o PC ou perder a conexão. Se a porta local já estiver em uso, um túnel anterior pode estar ativo.

O modelo padrão é `llama3`; ajuste `OLLAMA_MODEL` no `.env` se usa outro. A integração usa a API documentada em https://docs.ollama.com/api/chat.

Hora e data funcionam sem IA. Clima precisa de `OPENWEATHER_API_KEY`. Pesquisa web usa a dependência opcional `ddgs` (`pip install ddgs`), cuja instalação no Termux não foi validada.

## O que foi transferido

O pacote inclui código e documentação. Sua memória pessoal e seu `.env` não estão no ZIP. O celular inicia uma memória separada. Para levar o histórico, feche o Omega nos dois dispositivos e copie `memoria.json` para `~/omega-g31/omega/`; os históricos não são sincronizados automaticamente.

A interface Tkinter e a voz do Windows permanecem disponíveis no PC. No G31, esta entrega funciona pelo terminal; não inclui escuta contínua nem um aplicativo Android nativo.

## Verificação

Os testes automatizados simulam SSH e Wake-on-LAN para não desligar o computador durante a verificação. A instalação e a execução reais no G31 precisam ser verificadas no aparelho.
