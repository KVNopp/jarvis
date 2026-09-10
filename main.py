"""Omega: conversa direta no terminal, sem login."""
import functions
from brain import ollama_brain
from config import MODELO
from memory import ErroMemoria, carregar_memoria, salvar_memoria

AJUDA = '''Comandos
  /ajuda              Mostrar esta ajuda
  /hora ou /data      Consultar sem depender da IA
  /clima São Paulo   Consultar o clima de uma cidade
  /buscar assunto    Pesquisar na web
  /memoria           Ver quantas mensagens estão guardadas
  /sair              Encerrar
Você também pode perguntar normalmente.'''

AVISO_PENSANDO = '  Omega pensando...'


def limpar_aviso_pensando():
    print('\r' + ' ' * len(AVISO_PENSANDO) + '\r', end='', flush=True)


class CidadeNecessaria(Exception):
    """A interface deve pedir a cidade antes de continuar a consulta."""


def responder(pergunta, memoria, *, interativo=True):
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
            if pergunta.startswith('/') and pergunta.split()[0].lower() not in {'/hora', '/data', '/clima', '/buscar'}:
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
        except (functions.ErroServico, ollama_brain.ErroIA, ErroMemoria) as exc:
            print(f'\nOmega: {exc}')
        except (EOFError, KeyboardInterrupt):
            break
    print('\nAté logo!')
    return 0



if __name__ == '__main__':
    raise SystemExit(executar())
