"""Controle explícito do PC pela rede local, independente da IA."""
import os
import re
import socket
import subprocess
import unicodedata
from pathlib import Path


class ErroPC(Exception):
    pass


def pedido_energia(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                    if unicodedata.category(c) != 'Mn')
    texto = ' '.join(texto.split()).strip(' .!?')
    if texto in {'/ligar', '/desligar'}:
        return texto[1:]
    texto = re.sub(r'^omega[, ]+', '', texto)
    texto = re.sub(r'^por favor[, ]+', '', texto)
    texto = re.sub(r'[, ]+por favor$', '', texto)
    match = re.fullmatch(r'(liga|ligue|ligar|desliga|desligue|desligar) (?:o |meu )?(?:pc|computador)', texto)
    if match:
        return 'desligar' if match[1].startswith('deslig') else 'ligar'
    return None


def executar(acao):
    if acao == 'ligar':
        try:
            mac = bytes.fromhex(re.sub('[:-]', '', os.getenv('PC_MAC', '74563CB40C65')))
            if len(mac) != 6:
                raise ValueError('MAC precisa ter seis bytes')
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexao:
                conexao.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                conexao.sendto(b'\xff' * 6 + mac * 16,
                              (os.getenv('PC_BROADCAST', '192.168.15.255'), 9))
        except (OSError, ValueError) as exc:
            raise ErroPC('Não consegui enviar o sinal. Confira PC_MAC, PC_BROADCAST e a rede.') from exc
        return 'Sinal para ligar enviado ao PC. Aguarde a inicialização.'
    if acao != 'desligar':
        raise ErroPC('Use ligar pc ou desligar pc.')
    chave = Path(os.getenv('PC_SSH_KEY', '~/.ssh/pc_controle')).expanduser()
    if not chave.is_file():
        raise ErroPC(f'Chave SSH não encontrada: {chave}. Use a chave já configurada no G31.')
    comando = ['ssh', '-i', str(chave), '-o', 'IdentitiesOnly=yes',
               '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
               '-l', os.getenv('PC_USER', r'kvn-opp\keven'),
               os.getenv('PC_IP', '192.168.15.2'), 'shutdown.exe /s /t 0']
    try:
        resultado = subprocess.run(comando, shell=False, capture_output=True,
                                   text=True, timeout=20)
    except subprocess.TimeoutExpired as exc:
        raise ErroPC('O SSH demorou demais. Verifique o estado do PC antes de tentar novamente.') from exc
    except OSError as exc:
        raise ErroPC('Não consegui executar SSH. No Termux, use: pkg install openssh') from exc
    if resultado.returncode:
        detalhe = resultado.stderr.strip() or resultado.stdout.strip() or 'Conexão interrompida.'
        raise ErroPC(f'O SSH terminou com erro; confira o PC. {detalhe}')
    return 'Comando de desligamento enviado ao Windows.'
