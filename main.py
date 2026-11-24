"""Omega: conversa direta no terminal, sem login."""
import functions
import computer
import life_os
import pc_remoto
import sys
from brain import ollama_brain
from config import MODELO
from memory import ErroMemoria, carregar_memoria, salvar_memoria

AJUDA = '''Comandos
  /ajuda              Mostrar esta ajuda
  /hora ou /data      Consultar sem depender da IA
  /clima São Paulo   Consultar o clima de uma cidade
  /buscar assunto    Pesquisar na web
  /abrir aplicativo  Abrir um aplicativo no computador
  /apps              Listar aplicativos compatíveis
  /ligar             Ligar o PC pela rede local
  /desligar          Desligar o PC por SSH (imediato)
LIFE OS
  /hoje              Tarefas e hábitos de hoje
  /tarefas           Listar tarefas abertas
  /tarefa nome amanhã  Criar tarefa (prazo opcional: hoje, amanhã, 05/12)
  /feito nome        Concluir uma tarefa
  /habito nome       Marcar um hábito como feito hoje
  /lifeos entrar     Entrar na conta do LIFE OS (só no terminal)
  /lifeos            Ver a conexão; /lifeos sair desconecta
  /memoria          Ver quantas mensagens estão guardadas
  /sair              Encerrar
Você também pode perguntar normalmente.'''

AVISO_PENSANDO = '  Omega pensando...'
COMANDOS = {'/hora', '/data', '/clima', '/buscar', '/abrir', '/apps', '/ligar', '/desligar'}
ERROS = (functions.ErroServico, pc_remoto.ErroPC, ollama_brain.ErroIA, ErroMemoria, life_os.ErroLifeOS)


def comando_conhecido(pergunta):
    """Texto livre sempre vale; comandos com / precisam existir."""
    if not pergunta.startswith('/'):
        return True
    return pergunta.split()[0].lower() in COMANDOS or life_os.pedido(pergunta) is not None


def eh_login_lifeos(pergunta):
    return life_os.pedido(pergunta) == ('entrar', ())


def limpar_aviso_pensando():
    print('\r' + ' ' * len(AVISO_PENSANDO) + '\r', end='', flush=True)


class CidadeNecessaria(Exception):
    """A interface deve pedir a cidade antes de continuar a consulta."""


def responder(pergunta, memoria, *, interativo=True):
    acao = pc_remoto.pedido_energia(pergunta)
    if acao:
        return pc_remoto.executar(acao)
    if pergunta.strip().lower() == '/apps':
        return computer.listar_apps()
    aplicativo = computer.pedido_abertura(pergunta)
    if aplicativo is not None:
        return computer.abrir_app(aplicativo)
    pedido_lifeos = life_os.pedido(pergunta)
    if pedido_lifeos:
        return life_os.executar(*pedido_lifeos)
    comando, _, argumento = pergunta.partition(' ')
    rotas = {'/hora': 'HORA', '/data': 'DATA', '/clima': 'CLIMA', '/buscar': 'WEB'}
    if comando.lower() in rotas:
        intencao, consulta = rotas[comando.lower()], argumento.strip()
    else:
        intencao, consulta = ollama_brain.analisar_pergunta(pergunta, memoria)
    if intencao == 'HORA':
        return f'Agora são {functions.obter_hora()}.'
    if intencao == 'DATA':
        return f'Hoje é {functions.obter_data()}.'
    if intencao == 'CLIMA':
        if not consulta and not interativo:
            raise CidadeNecessaria()
        if not consulta:
            limpar_aviso_pensando()
        cidade = consulta or input('Cidade: ').strip()
        if not cidade:
            raise functions.ErroServico('Informe uma cidade usando /clima nome da cidade.')
        return functions.obter_clima(cidade)
    if intencao == 'WEB':
        consulta = consulta or pergunta
        if interativo:
            limpar_aviso_pensando()
            print(f'  Pesquisando: {consulta}')
        fontes = functions.buscar_na_web(consulta)
        resposta = ollama_brain.perguntar(pergunta, memoria, contexto_web=fontes)
        return resposta + '\n\nFontes consultadas:\n' + '\n'.join(f"- {f['title']}: {f['href']}" for f in fontes)
    return ollama_brain.perguntar(pergunta, memoria)



def executar():
    try:
        memoria = carregar_memoria()
    except ErroMemoria as exc:
        print(f'Omega: {exc}')
        return 1
    print('\n' + '=' * 48)
    print('  OMEGA | Seu assistente pessoal')
    print(f'  Modelo: {MODELO} | Memória: {len(memoria)} registros')
    print('  Converse diretamente. Digite /ajuda para comandos.')
    print('=' * 48)
    while True:
        try:
            pergunta = input('\nVocê > ').strip()
            if not pergunta:
                continue
            comando = pergunta.lower()
            if comando in {'/sair', 'sair', 'exit', 'quit'}:
                break
            if comando == '/ajuda':
                print(AJUDA)
                continue
            if comando == '/memoria':
                print(f'Omega: {len(memoria)} registros preservados em memoria.json.')
                continue
            if eh_login_lifeos(pergunta):
                print('Omega: ' + life_os.entrar_interativo())
                continue
            if not comando_conhecido(pergunta):
                print('Comando desconhecido. Digite /ajuda.')
                continue
            print(AVISO_PENSANDO, end='', flush=True)
            try:
                resposta = responder(pergunta, memoria)
            finally:
                limpar_aviso_pensando()
            nova_memoria = memoria + [{'role': 'user', 'content': pergunta}, {'role': 'assistant', 'content': resposta}]
            print(f'\nOmega > {resposta}')
            salvar_memoria(nova_memoria)
            memoria = nova_memoria
        except ERROS as exc:
            print(f'\nOmega: {exc}')
        except (EOFError, KeyboardInterrupt):
            break
    print('\nAté logo!')
    return 0



def executar_argumentos(argumentos):
    if not argumentos:
        return executar()
    pergunta = ' '.join(argumentos)
    if pergunta in {'--help', '-h', '/ajuda'}:
        print(AJUDA)
        return 0
    try:
        # Controle do PC independe da IA e de um arquivo de memória válido.
        acao = pc_remoto.pedido_energia(pergunta)
        if acao:
            print('Omega: ' + pc_remoto.executar(acao))
            return 0
        if eh_login_lifeos(pergunta):
            print('Omega: ' + life_os.entrar_interativo())
            return 0
        memoria = carregar_memoria()
        resposta = responder(pergunta, memoria, interativo=False)
        print('Omega: ' + resposta)
        salvar_memoria(memoria + [{'role': 'user', 'content': pergunta},
                                  {'role': 'assistant', 'content': resposta}])
        return 0
    except CidadeNecessaria:
        print('Omega: Informe a cidade: omega /clima nome da cidade')
        return 1
    except ERROS as exc:
        print(f'Omega: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(executar_argumentos(sys.argv[1:]))
