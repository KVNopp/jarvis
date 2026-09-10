"""Abertura de aplicativos conhecidos, sem shell ou argumentos do modelo."""
import os
import re
import subprocess
import unicodedata
from pathlib import Path

from functions import ErroServico

APPS = {
    'calculadora': ('Calculadora', ('calc.exe',), ()),
    'bloco de notas': ('Bloco de Notas', ('notepad.exe',), ()),
    'paint': ('Paint', ('mspaint.exe',), (('LOCALAPPDATA', 'Microsoft/WindowsApps/mspaint.exe'),)),
    'explorador': ('Explorador de Arquivos', (), (('SystemRoot', 'explorer.exe'),)),
    'chrome': ('Google Chrome', (), (('ProgramFiles', 'Google/Chrome/Application/chrome.exe'),
                                   ('ProgramFiles(x86)', 'Google/Chrome/Application/chrome.exe'),
                                   ('LOCALAPPDATA', 'Google/Chrome/Application/chrome.exe'))),
    'edge': ('Microsoft Edge', (), (('ProgramFiles(x86)', 'Microsoft/Edge/Application/msedge.exe'),
                                  ('ProgramFiles', 'Microsoft/Edge/Application/msedge.exe'))),
    'vscode': ('Visual Studio Code', (), (('LOCALAPPDATA', 'Programs/Microsoft VS Code/Code.exe'),
                                        ('ProgramFiles', 'Microsoft VS Code/Code.exe'))),
    'spotify': ('Spotify', (), (('APPDATA', 'Spotify/Spotify.exe'),)),
}
ALIASES = {'calc': 'calculadora', 'notepad': 'bloco de notas', 'bloco': 'bloco de notas',
           'explorador de arquivos': 'explorador', 'explorer': 'explorador',
           'google chrome': 'chrome', 'google': 'chrome', 'microsoft edge': 'edge',
           'vs code': 'vscode', 'visual studio code': 'vscode', 'codigo': 'vscode'}


def normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                           if unicodedata.category(c) != 'Mn').split())


def pedido_abertura(pergunta):
    """Só a mensagem atual pode solicitar uma ação; histórico e IA não executam apps."""
    texto = normalizar(pergunta).strip()
    if texto == '/abrir' or texto.startswith('/abrir '):
        return texto[6:].strip()
    texto = re.sub(r'^omega[, ]+', '', texto)
    texto = re.sub(r'^por favor[, ]+', '', texto)
    pedido = re.fullmatch(
        r'(?:abra|abre|abrir|inicie|iniciar|'
        r'(?:(?:voce )?(?:pode|poderia|consegue)|tente|tenta|quero que voce tente) abrir|'
        r'quero que voce (?:abra|inicie))\s+(?:(?:o|a)\s+)?(.+)', texto)
    if not pedido:
        return None
    nome = re.sub(r'[, ]*por favor[.!?]*$', '', pedido.group(1)).strip(' .!?')
    return nome


def listar_apps():
    return 'Aplicativos disponíveis para abertura: ' + ', '.join(v[0] for v in APPS.values()) + '. Use /abrir nome do aplicativo.'


def localizar_app(chave):
    _, sistema, locais = APPS[chave]
    candidatos = []
    if os.environ.get('SystemRoot'):
        candidatos.extend(Path(os.environ['SystemRoot']) / 'System32' / nome for nome in sistema)
    for variavel, caminho in locais:
        if os.environ.get(variavel):
            candidatos.append(Path(os.environ[variavel]) / caminho)
    return next((p for p in candidatos if p.is_file()), None)


def abrir_app(nome):
    chave = normalizar(nome)
    chave = ALIASES.get(chave, chave)
    if not chave:
        return listar_apps()
    if chave not in APPS:
        raise ErroServico('Esse aplicativo ainda não está cadastrado. ' + listar_apps())
    if os.name != 'nt':
        raise ErroServico('A abertura de aplicativos está disponível no Windows.')
    caminho = localizar_app(chave)
    if caminho is None:
        raise ErroServico(f'Não encontrei {APPS[chave][0]} nos locais de instalação conhecidos.')
    try:
        subprocess.Popen([str(caminho)], shell=False, cwd=str(caminho.parent),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise ErroServico(f'Não consegui iniciar {APPS[chave][0]}. Confira a instalação.') from exc
    return f'Solicitei ao Windows a abertura de {APPS[chave][0]}.'
