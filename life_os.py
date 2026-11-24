"""Ponte entre o Omega e o LIFE OS (tarefas, hábitos e resumo do dia).

Fala direto com o Supabase do LIFE OS pela API REST, usando só `requests`,
e grava no mesmo formato do app: cada item é um registro
{id, collection, data, updated_at, deleted}. Vence a edição mais recente.
"""
import datetime
import json
import os
import re
import time
import unicodedata
import uuid
from pathlib import Path

import requests

DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
TIMEOUT = (5, 20)


class ErroLifeOS(Exception):
    pass


# ---------- texto e datas ----------
def _sem_acento(texto):
    # Um caractere de entrada vira exatamente um de saída, para recortar o original pelas posições.
    return ''.join(unicodedata.normalize('NFD', c)[0] for c in texto).lower()


def _chave(texto):
    return ' '.join(_sem_acento(texto).split())


def _iso(data):
    return data.isoformat()


def _dia_da_semana(data):
    """0 = domingo, como o getDay() do JavaScript usado no app."""
    return (data.weekday() + 1) % 7


def _data_curta(iso, hoje):
    data = datetime.date.fromisoformat(iso)
    if data == hoje:
        return 'hoje'
    if data == hoje + datetime.timedelta(days=1):
        return 'amanhã'
    if data == hoje - datetime.timedelta(days=1):
        return 'ontem'
    return data.strftime('%d/%m') if data.year == hoje.year else data.strftime('%d/%m/%Y')


_PRAZO = re.compile(r'\s+(?:(?:pra|para)\s+)?(?:(depois de amanha)|(amanha)|(hoje)|'
                    r'(\d{1,2})/(\d{1,2})(?:/(\d{4}))?)$')


def _separar_prazo(original, hoje):
    """'Estudar física amanhã' -> ('Estudar física', '2026-11-25')."""
    achado = _PRAZO.search(_sem_acento(original))
    if not achado:
        return original.strip(), None
    depois, amanha, hj, dia, mes, ano = achado.groups()
    if depois:
        data = hoje + datetime.timedelta(days=2)
    elif amanha:
        data = hoje + datetime.timedelta(days=1)
    elif hj:
        data = hoje
    else:
        try:
            data = datetime.date(int(ano) if ano else hoje.year, int(mes), int(dia))
        except ValueError:
            return original.strip(), None
        if not ano and data < hoje:
            data = data.replace(year=data.year + 1)
    titulo = original[:achado.start()].strip(' :,')
    if not titulo:
        return original.strip(), None
    return titulo, _iso(data)


# ---------- entendimento dos pedidos ----------
_FRASES = [
    ('tarefa', r'(?:cri[ae]r?|adicion[ae]r?|anot[ae]r?|coloc[ae]r?|registr[ae]r?|nova)\s+'
               r'(?:(?:uma|a)\s+)?(?:nova\s+)?tarefa\s*:?\s+(?P<arg>.+)'),
    ('feito', r'(?:terminei|conclui|concluir|finalizei|fiz)\s+a\s+tarefa\s*:?\s+(?P<arg>.+)'),
    ('feito', r'marcar?\s+a\s+tarefa\s+(?P<arg>.+?)\s+como\s+(?:feita|concluida)'),
    ('habito', r'(?:marquei|marcar?|fiz|cumpri)\s+o\s+habito\s+(?:de\s+)?(?P<arg>.+?)(?:\s+hoje)?'),
    ('hoje', r'o que (?:eu )?tenho (?:pra|para) hoje|como (?:esta|ta) (?:o )?meu dia|'
             r'resumo do (?:meu )?dia|minha agenda(?: de hoje)?'),
    ('tarefas', r'(?:quais sao )?(?:as )?minhas tarefas|listar? (?:as )?(?:minhas )?tarefas'),
]
_COMANDOS = {'/tarefas': 'tarefas', '/hoje': 'hoje', '/lifeos': 'status',
             '/lifeos entrar': 'entrar', '/lifeos sair': 'sair'}
_COM_ARGUMENTO = {'/tarefa': 'tarefa', '/feito': 'feito', '/habito': 'habito'}


def pedido(texto, hoje=None):
    """Devolve (ação, argumentos) quando o texto é um pedido para o LIFE OS; senão None."""
    hoje = hoje or datetime.date.today()
    original = ' '.join(texto.split())
    norm = _sem_acento(original)
    if len(norm) != len(original):  # caractere incomum; trabalha só com o texto normalizado
        original = norm
    if norm in _COMANDOS:
        return _COMANDOS[norm], ()
    comando, _, resto = norm.partition(' ')
    if comando in _COM_ARGUMENTO:
        argumento = original[len(comando) + 1:].strip(' .!?')
        if not argumento:
            return None
        acao = _COM_ARGUMENTO[comando]
        return (acao, _separar_prazo(argumento, hoje)) if acao == 'tarefa' else (acao, (argumento,))
    if norm.startswith('/'):
        return None
    # Remove "Omega," / "por favor" do começo e pontuação do fim, mantendo as posições.
    inicio = re.match(r'(?:(?:omega|por favor)[, ]+)*', norm).end()
    fim = len(norm.rstrip(' .!?'))
    norm, original = norm[inicio:fim], original[inicio:fim]
    for acao, padrao in _FRASES:
        achado = re.fullmatch(padrao, norm)
        if not achado:
            continue
        if 'arg' not in achado.groupdict():
            return acao, ()
        argumento = original[achado.start('arg'):achado.end('arg')].strip(' :,')
        if acao == 'tarefa':
            return acao, _separar_prazo(argumento, hoje)
        return acao, (argumento,)
    return None


# ---------- cliente do Supabase ----------
class Cliente:
    def __init__(self, url, chave, sessao_path, http=requests,
                 hoje=datetime.date.today, agora_ms=lambda: int(time.time() * 1000)):
        self.url = (url or '').strip().rstrip('/')
        self.chave = (chave or '').strip()
        self.sessao_path = Path(sessao_path)
        self.http = http
        self.hoje = hoje
        self.agora_ms = agora_ms

    # ----- configuração e sessão -----
    def _exigir_configuracao(self):
        if not self.url or not self.chave:
            raise ErroLifeOS('Configure LIFEOS_SUPABASE_URL e LIFEOS_SUPABASE_KEY no .env '
                             '(os mesmos valores de Ajustes > Projeto Supabase no LIFE OS).')

    def _cabecalhos(self, token=None):
        cabecalhos = {'apikey': self.chave, 'Content-Type': 'application/json'}
        cabecalhos['Authorization'] = 'Bearer ' + (token or self.chave)
        return cabecalhos

    def _chamar(self, metodo, caminho, **kw):
        try:
            return getattr(self.http, metodo)(self.url + caminho, timeout=TIMEOUT, **kw)
        except requests.RequestException as exc:
            raise ErroLifeOS('Sem conexão com o Supabase do LIFE OS. Verifique a internet.') from exc

    def _ler_sessao(self):
        try:
            return json.loads(self.sessao_path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            return None

    def _salvar_sessao(self, dados):
        temporario = self.sessao_path.with_suffix('.tmp')
        temporario.write_text(json.dumps(dados), encoding='utf-8')
        os.replace(temporario, self.sessao_path)

    def _guardar_token(self, resposta, email=None):
        dados = resposta.json()
        anterior = self._ler_sessao() or {}
        usuario = dados.get('user') or {}
        self._salvar_sessao({
            'access_token': dados['access_token'],
            'refresh_token': dados['refresh_token'],
            'expires_at': dados.get('expires_at') or time.time() + dados.get('expires_in', 3600),
            'email': usuario.get('email') or email or anterior.get('email'),
        })

    def entrar(self, email, senha):
        self._exigir_configuracao()
        resposta = self._chamar('post', '/auth/v1/token', params={'grant_type': 'password'},
                                headers=self._cabecalhos(), json={'email': email, 'password': senha})
        if resposta.status_code != 200:
            texto = resposta.text or ''
            if 'Invalid login credentials' in texto:
                raise ErroLifeOS('E-mail ou senha incorretos.')
            if 'Email not confirmed' in texto:
                raise ErroLifeOS('Confirme seu e-mail pelo link do Supabase e tente de novo.')
            raise ErroLifeOS(f'O Supabase recusou o login (código {resposta.status_code}).')
        self._guardar_token(resposta, email)
        return f'Conectado ao LIFE OS como {email}.'

    def sair(self):
        sessao = self._ler_sessao()
        if sessao and self.url:
            try:
                self._chamar('post', '/auth/v1/logout', headers=self._cabecalhos(sessao['access_token']))
            except ErroLifeOS:
                pass  # sem rede: apagar a sessão local já basta
        self.sessao_path.unlink(missing_ok=True)
        return 'Omega desconectado do LIFE OS.'

    def status(self):
        if not self.url or not self.chave:
            return 'LIFE OS não configurado. Preencha LIFEOS_SUPABASE_URL e LIFEOS_SUPABASE_KEY no .env.'
        sessao = self._ler_sessao()
        if not sessao:
            return 'LIFE OS configurado, mas sem login. Use /lifeos entrar no terminal.'
        return f"Conectado ao LIFE OS como {sessao.get('email') or 'sua conta'}."

    def _renovar(self, sessao):
        resposta = self._chamar('post', '/auth/v1/token', params={'grant_type': 'refresh_token'},
                                headers=self._cabecalhos(), json={'refresh_token': sessao['refresh_token']})
        if resposta.status_code != 200:
            self.sessao_path.unlink(missing_ok=True)
            raise ErroLifeOS('Sua sessão do LIFE OS expirou. Entre de novo com /lifeos entrar.')
        self._guardar_token(resposta)
        return self._ler_sessao()['access_token']

    def _token(self, forcar_renovacao=False):
        self._exigir_configuracao()
        sessao = self._ler_sessao()
        if not sessao or 'refresh_token' not in sessao:
            raise ErroLifeOS('Entre na sua conta do LIFE OS primeiro: /lifeos entrar (no terminal).')
        if forcar_renovacao or float(sessao.get('expires_at', 0)) < time.time() + 60:
            return self._renovar(sessao)
        return sessao['access_token']

    def _api(self, metodo, caminho, **kw):
        resposta = self._chamar(metodo, caminho, headers=self._cabecalhos(self._token()), **kw)
        if resposta.status_code == 401:
            resposta = self._chamar(metodo, caminho, headers=self._cabecalhos(self._token(True)), **kw)
        if resposta.status_code >= 400:
            if re.search(r'does not exist|schema cache|Could not find', resposta.text or ''):
                raise ErroLifeOS('A tabela do LIFE OS não existe nesse Supabase. Rode o supabase/schema.sql.')
            raise ErroLifeOS(f'O Supabase do LIFE OS respondeu com erro {resposta.status_code}.')
        return resposta

    # ----- leitura e gravação de registros -----
    def _registros(self, *colecoes):
        linhas, inicio = [], 0
        while True:
            lote = self._api('get', '/rest/v1/records', params={
                'select': 'id,collection,data,updated_at,deleted',
                'collection': 'in.(' + ','.join(colecoes) + ')',
                'deleted': 'eq.false', 'order': 'id', 'limit': 1000, 'offset': inicio,
            }).json()
            linhas.extend(lote)
            if len(lote) < 1000:
                return linhas
            inicio += 1000

    def _registro(self, id_):
        lote = self._api('get', '/rest/v1/records', params={
            'select': 'id,collection,data,updated_at,deleted', 'id': 'eq.' + id_}).json()
        return lote[0] if lote else None

    def _gravar(self, colecao, id_, dados, anterior=None):
        agora = self.agora_ms()
        updated_at = max(agora, int(anterior['updated_at']) + 1) if anterior else agora
        linha = {'id': id_, 'collection': colecao, 'data': dados, 'updated_at': updated_at, 'deleted': False}
        gravados = self._api('post', '/rest/v1/rpc/sync_push', json={'rows': [linha]}).json()
        if gravados != 1:
            raise ErroLifeOS('Esse item acabou de ser alterado em outro aparelho. Tente de novo.')

    @staticmethod
    def _encontrar(registros, nome, campo, tipo):
        procurado = _chave(nome)
        exatos = [r for r in registros if _chave(str(r['data'].get(campo, ''))) == procurado]
        if len(exatos) == 1:
            return exatos[0]
        parecidos = exatos or [r for r in registros if procurado in _chave(str(r['data'].get(campo, '')))]
        if not parecidos:
            raise ErroLifeOS(f'Não encontrei {tipo} "{nome}" no LIFE OS.')
        if len(parecidos) > 1:
            nomes = ', '.join(sorted(str(r['data'].get(campo)) for r in parecidos))
            raise ErroLifeOS(f'Encontrei mais de um(a) {tipo}: {nomes}. Diga o nome completo.')
        return parecidos[0]

    # ----- ações -----
    def adicionar_tarefa(self, titulo, prazo=None):
        self._token()
        titulo = titulo.strip()
        if not titulo:
            raise ErroLifeOS('Diga o nome da tarefa, por exemplo: /tarefa Estudar física amanhã')
        self._gravar('tasks', str(uuid.uuid4()), {'title': titulo, 'due': prazo, 'done': False,
                                                  'goal_id': None, 'created': self.agora_ms()})
        quando = f' para {_data_curta(prazo, self.hoje())}' if prazo else ''
        return f'Tarefa "{titulo}" criada no LIFE OS{quando}.'

    def concluir_tarefa(self, nome):
        abertas = [r for r in self._registros('tasks') if not r['data'].get('done')]
        tarefa = self._encontrar(abertas, nome, 'title', 'tarefa')
        dados = dict(tarefa['data'], done=True, done_at=self.agora_ms())
        self._gravar('tasks', tarefa['id'], dados, tarefa)
        return f'Tarefa "{dados["title"]}" concluída no LIFE OS.'

    def marcar_habito(self, nome):
        habito = self._encontrar(self._registros('habits'), nome, 'name', 'hábito')
        hoje = _iso(self.hoje())
        id_ = f"hl_{habito['id']}_{hoje}"
        anterior = self._registro(id_)
        nome_habito = habito['data'].get('name')
        if anterior and not anterior['deleted'] and anterior['data'].get('done'):
            return f'O hábito "{nome_habito}" já estava marcado hoje.'
        self._gravar('habit_logs', id_, {'habit_id': habito['id'], 'date': hoje, 'done': True}, anterior)
        return f'Hábito "{nome_habito}" marcado hoje no LIFE OS.'

    def _tarefas_abertas(self, registros):
        tarefas = [r['data'] for r in registros if r['collection'] == 'tasks' and not r['data'].get('done')]
        return sorted(tarefas, key=lambda t: (t.get('due') or '9999', t.get('created') or 0))

    def resumo_hoje(self):
        registros = self._registros('tasks', 'habits', 'habit_logs')
        data = self.hoje()
        hoje = _iso(data)
        tarefas = self._tarefas_abertas(registros)
        atrasadas = [t for t in tarefas if t.get('due') and t['due'] < hoje]
        de_hoje = [t for t in tarefas if t.get('due') == hoje]
        feitos = {r['id'] for r in registros if r['collection'] == 'habit_logs' and r['data'].get('done')}
        habitos = [r for r in registros if r['collection'] == 'habits'
                   and _dia_da_semana(data) in (r['data'].get('days') or range(7))]
        habitos.sort(key=lambda r: (r['data'].get('order', 0), _chave(str(r['data'].get('name', '')))))

        linhas = [f"Hoje, {DIAS[data.weekday()]}, {data.strftime('%d/%m')}:"]
        if atrasadas:
            linhas.append('Tarefas atrasadas:')
            linhas += [f"  - {t['title']} (era {_data_curta(t['due'], data)})" for t in atrasadas]
        if de_hoje:
            linhas.append('Tarefas de hoje:')
            linhas += [f"  - {t['title']}" for t in de_hoje]
        if habitos:
            linhas.append('Hábitos de hoje:')
            for r in habitos:
                marca = 'x' if f"hl_{r['id']}_{hoje}" in feitos else ' '
                linhas.append(f"  [{marca}] {r['data'].get('name')}")
        if len(linhas) == 1:
            linhas.append('Nenhuma tarefa nem hábito para hoje.')
        return '\n'.join(linhas)

    def listar_tarefas(self):
        data = self.hoje()
        hoje = _iso(data)
        tarefas = self._tarefas_abertas(self._registros('tasks'))
        grupos = [
            ('Atrasadas', [t for t in tarefas if t.get('due') and t['due'] < hoje]),
            ('Hoje', [t for t in tarefas if t.get('due') == hoje]),
            ('Próximas', [t for t in tarefas if t.get('due') and t['due'] > hoje]),
            ('Sem data', [t for t in tarefas if not t.get('due')]),
        ]
        linhas = []
        for nome, itens in grupos:
            if itens:
                linhas.append(nome + ':')
                for t in itens:
                    prazo = f" ({_data_curta(t['due'], data)})" if t.get('due') and t['due'] != hoje else ''
                    linhas.append(f"  - {t['title']}{prazo}")
        return '\n'.join(linhas) if linhas else 'Nenhuma tarefa aberta no LIFE OS.'


# ---------- uso pelo Omega ----------
def cliente_padrao():
    from config import BASE_DIR
    return Cliente(os.getenv('LIFEOS_SUPABASE_URL', ''), os.getenv('LIFEOS_SUPABASE_KEY', ''),
                   BASE_DIR / 'lifeos_sessao.json')


def entrar_interativo(cliente=None, ler=input, ler_senha=None):
    import getpass
    cliente = cliente or cliente_padrao()
    cliente._exigir_configuracao()
    email = ler('E-mail do LIFE OS: ').strip()
    senha = (ler_senha or getpass.getpass)('Senha (não aparece ao digitar): ')
    if not email or not senha:
        raise ErroLifeOS('Login cancelado.')
    return cliente.entrar(email, senha)


def executar(acao, argumentos, cliente=None):
    cliente = cliente or cliente_padrao()
    if acao == 'tarefa':
        return cliente.adicionar_tarefa(*argumentos)
    if acao == 'feito':
        return cliente.concluir_tarefa(*argumentos)
    if acao == 'habito':
        return cliente.marcar_habito(*argumentos)
    if acao == 'hoje':
        return cliente.resumo_hoje()
    if acao == 'tarefas':
        return cliente.listar_tarefas()
    if acao == 'status':
        return cliente.status()
    if acao == 'sair':
        return cliente.sair()
    if acao == 'entrar':
        raise ErroLifeOS('Faça o login no terminal: python main.py /lifeos entrar')
    raise ErroLifeOS('Pedido do LIFE OS não reconhecido.')
