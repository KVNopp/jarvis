"""Memória compatível com o arquivo original, sem migração destrutiva."""
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from config import MEMORIA_PATH, PROMPT

class ErroMemoria(Exception):
    pass

def carregar_memoria(nome_arquivo=MEMORIA_PATH):
    try:
        dados = json.loads(Path(nome_arquivo).read_text(encoding='utf-8-sig'))
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as exc:
        raise ErroMemoria('Não consegui ler a memória. O arquivo foi preservado; confira o JSON ou restaure um backup.') from exc
    if not isinstance(dados, list) or any(
        not isinstance(m, dict) or m.get('role') not in {'system', 'user', 'assistant'}
        or not isinstance(m.get('content'), str) for m in dados
    ):
        raise ErroMemoria('Formato de memória inválido. O arquivo foi preservado.')
    return dados

def salvar_memoria(memoria, nome_arquivo=MEMORIA_PATH):
    caminho = Path(nome_arquivo)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=caminho.parent,
                                         prefix=caminho.name + '.', suffix='.tmp', delete=False) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(memoria, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        if caminho.exists():
            carregar_memoria(caminho)
            shutil.copy2(caminho, caminho.with_suffix(caminho.suffix + '.bak'))
        os.replace(temporario, caminho)
    except OSError as exc:
        raise ErroMemoria('Não consegui salvar a conversa. Confira espaço e permissões da pasta.') from exc
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()

def montar_contexto(historico, pergunta, limite=16000):
    """Seleciona mensagens recentes e trechos antigos; não modifica o histórico."""
    mensagens = [m for m in historico if m['role'] != 'system']
    recentes = []
    usado = 0
    for item in reversed(mensagens):
        restante = int(limite * .7) - usado
        if len(recentes) >= 16 or restante <= 0:
            break
        conteudo = item['content'][-min(4000, restante):]
        recentes.insert(0, {'role': item['role'], 'content': conteudo})
        usado += len(conteudo)
    antigas = mensagens[:len(mensagens) - len(recentes)]
    termos = set(re.findall(r'\w{4,}', pergunta.lower()))
    relevantes = sorted(antigas, key=lambda m: len(termos & set(re.findall(r'\w{4,}', m['content'].lower()))), reverse=True)
    lembrancas = []
    for item in relevantes:
        if not termos.intersection(re.findall(r'\w{4,}', item['content'].lower())):
            continue
        trecho = item['content'][:min(1500, limite - usado)]
        if not trecho or len(lembrancas) >= 4:
            break
        lembrancas.append(f"{item['role']}: {trecho}")
        usado += len(trecho)
    contexto = [{'role': 'system', 'content': PROMPT}]
    if lembrancas:
        contexto.append({'role': 'user', 'content': 'Trechos antigos do histórico (podem estar desatualizados):\n' + '\n'.join(lembrancas)})
    return contexto + recentes
