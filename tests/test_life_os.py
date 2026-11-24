import datetime
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import life_os

URL = 'https://projeto.supabase.co'
HOJE = datetime.date(2026, 11, 24)  # terça-feira
AGORA = 1_800_000_000_000


class Resposta:
    def __init__(self, status, dados):
        self.status_code = status
        self._dados = dados
        self.text = json.dumps(dados)

    def json(self):
        return self._dados


class SupabaseFalso:
    """Imita o Auth e a tabela records do LIFE OS, inclusive a regra do sync_push."""

    def __init__(self):
        self.registros = {}
        self.logins = 0
        self.refreshes = 0
        self.token_valido = 'token-1'

    def _autorizado(self, headers):
        return headers.get('apikey') == 'chave' and headers.get('Authorization') == 'Bearer ' + self.token_valido

    def post(self, url, json=None, headers=None, params=None, timeout=None):
        caminho = urlparse(url).path
        if caminho == '/auth/v1/token':
            tipo = (params or {}).get('grant_type')
            if tipo == 'password':
                if json != {'email': 'eu@exemplo.com', 'password': 'segredo'}:
                    return Resposta(400, {'error_description': 'Invalid login credentials'})
                self.logins += 1
            elif tipo == 'refresh_token':
                if json != {'refresh_token': 'refresh-1'}:
                    return Resposta(400, {'error_description': 'Invalid Refresh Token'})
                self.refreshes += 1
                self.token_valido = 'token-2'
            return Resposta(200, {'access_token': self.token_valido, 'refresh_token': 'refresh-1',
                                  'expires_at': 4_000_000_000, 'user': {'id': 'u1', 'email': 'eu@exemplo.com'}})
        if caminho == '/auth/v1/logout':
            return Resposta(204, None)
        if caminho == '/rest/v1/rpc/sync_push':
            if not self._autorizado(headers):
                return Resposta(401, {'message': 'JWT expired'})
            n = 0
            for linha in json['rows']:
                atual = self.registros.get(linha['id'])
                if atual is None or linha['updated_at'] > atual['updated_at']:
                    self.registros[linha['id']] = dict(linha)
                    n += 1
            return Resposta(200, n)
        return Resposta(404, {'message': 'não encontrado'})

    def get(self, url, headers=None, params=None, timeout=None):
        if not self._autorizado(headers):
            return Resposta(401, {'message': 'JWT expired'})
        params = params or {}
        linhas = list(self.registros.values())
        if 'collection' in params:
            colecoes = params['collection'][len('in.('):-1].split(',')
            linhas = [r for r in linhas if r['collection'] in colecoes]
        if 'id' in params:
            linhas = [r for r in linhas if r['id'] == params['id'][len('eq.'):]]
        if params.get('deleted') == 'eq.false':
            linhas = [r for r in linhas if not r['deleted']]
        inicio = int(params.get('offset', 0))
        return Resposta(200, linhas[inicio:inicio + int(params.get('limit', 1000))])

    def criar(self, colecao, id_, dados, updated_at=1, deleted=False):
        self.registros[id_] = {'id': id_, 'collection': colecao, 'data': dados,
                               'updated_at': updated_at, 'deleted': deleted}


class LifeOSTestes(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.sessao = Path(self.pasta.name) / 'sessao.json'
        self.servidor = SupabaseFalso()
        self.cliente = life_os.Cliente(URL, 'chave', self.sessao, http=self.servidor,
                                       hoje=lambda: HOJE, agora_ms=lambda: AGORA)

    def tearDown(self):
        self.pasta.cleanup()

    def entrar(self):
        self.cliente.entrar('eu@exemplo.com', 'segredo')

    # ---------- sessão ----------
    def test_sem_configuracao_explica_o_que_falta(self):
        cliente = life_os.Cliente('', '', self.sessao, http=self.servidor)
        with self.assertRaisesRegex(life_os.ErroLifeOS, 'LIFEOS_SUPABASE_URL'):
            cliente.adicionar_tarefa('x')

    def test_sem_login_pede_para_entrar(self):
        with self.assertRaisesRegex(life_os.ErroLifeOS, '/lifeos entrar'):
            self.cliente.adicionar_tarefa('x')

    def test_login_errado_nao_salva_sessao(self):
        with self.assertRaisesRegex(life_os.ErroLifeOS, 'incorretos'):
            self.cliente.entrar('eu@exemplo.com', 'errada')
        self.assertFalse(self.sessao.exists())

    def test_login_salva_sessao_sem_senha(self):
        self.entrar()
        texto = self.sessao.read_text(encoding='utf-8')
        self.assertNotIn('segredo', texto)
        self.assertIn('refresh-1', texto)
        self.assertIn('eu@exemplo.com', self.cliente.status())

    def test_token_expirado_e_renovado(self):
        self.entrar()
        sessao = json.loads(self.sessao.read_text(encoding='utf-8'))
        sessao['expires_at'] = 10
        self.sessao.write_text(json.dumps(sessao), encoding='utf-8')
        self.cliente.adicionar_tarefa('Ler')
        self.assertEqual(self.servidor.refreshes, 1)
        self.assertEqual(json.loads(self.sessao.read_text())['access_token'], 'token-2')

    def test_sair_apaga_sessao(self):
        self.entrar()
        self.cliente.sair()
        self.assertFalse(self.sessao.exists())

    # ---------- tarefas ----------
    def test_adicionar_tarefa_no_formato_do_app(self):
        self.entrar()
        resposta = self.cliente.adicionar_tarefa('Estudar física', '2026-11-25')
        [registro] = self.servidor.registros.values()
        self.assertEqual(registro['collection'], 'tasks')
        self.assertEqual(registro['updated_at'], AGORA)
        self.assertFalse(registro['deleted'])
        self.assertEqual(registro['data'], {'title': 'Estudar física', 'due': '2026-11-25', 'done': False,
                                            'goal_id': None, 'created': AGORA})
        self.assertIn('Estudar física', resposta)
        self.assertIn('amanhã', resposta)

    def test_concluir_tarefa_preserva_campos_e_vence_versao_antiga(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Pagar conta', 'due': '2026-11-24', 'done': False,
                                            'goal_id': 'g1', 'created': 5}, updated_at=AGORA + 50)
        resposta = self.cliente.concluir_tarefa('pagar conta')
        registro = self.servidor.registros['t1']
        self.assertTrue(registro['data']['done'])
        self.assertEqual(registro['data']['done_at'], AGORA)
        self.assertEqual(registro['data']['goal_id'], 'g1')
        self.assertEqual(registro['updated_at'], AGORA + 51)
        self.assertIn('Pagar conta', resposta)

    def test_concluir_tarefa_ambigua_lista_opcoes(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Estudar física', 'done': False})
        self.servidor.criar('tasks', 't2', {'title': 'Estudar química', 'done': False})
        with self.assertRaisesRegex(life_os.ErroLifeOS, 'física.*química|química.*física'):
            self.cliente.concluir_tarefa('estudar')

    def test_concluir_tarefa_ignora_apagadas_e_feitas(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Ler', 'done': True})
        self.servidor.criar('tasks', 't2', {'title': 'Ler livro', 'done': False}, deleted=True)
        with self.assertRaisesRegex(life_os.ErroLifeOS, 'Não encontrei'):
            self.cliente.concluir_tarefa('ler')

    def test_nome_exato_vence_parecido(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Ler', 'done': False})
        self.servidor.criar('tasks', 't2', {'title': 'Ler livro', 'done': False})
        self.cliente.concluir_tarefa('ler')
        self.assertTrue(self.servidor.registros['t1']['data']['done'])
        self.assertFalse(self.servidor.registros['t2']['data']['done'])

    # ---------- hábitos ----------
    def test_marcar_habito_usa_id_do_app(self):
        self.entrar()
        self.servidor.criar('habits', 'h1', {'name': 'Leitura', 'days': [2]})
        resposta = self.cliente.marcar_habito('leitura')
        registro = self.servidor.registros['hl_h1_2026-11-24']
        self.assertEqual(registro['collection'], 'habit_logs')
        self.assertEqual(registro['data'], {'habit_id': 'h1', 'date': '2026-11-24', 'done': True})
        self.assertIn('Leitura', resposta)

    def test_marcar_habito_ja_feito_nao_duplica(self):
        self.entrar()
        self.servidor.criar('habits', 'h1', {'name': 'Leitura', 'days': []})
        self.servidor.criar('habit_logs', 'hl_h1_2026-11-24', {'habit_id': 'h1', 'date': '2026-11-24', 'done': True}, updated_at=7)
        resposta = self.cliente.marcar_habito('Leitura')
        self.assertIn('já estava', resposta)
        self.assertEqual(self.servidor.registros['hl_h1_2026-11-24']['updated_at'], 7)

    def test_remarcar_habito_desmarcado(self):
        self.entrar()
        self.servidor.criar('habits', 'h1', {'name': 'Leitura'})
        self.servidor.criar('habit_logs', 'hl_h1_2026-11-24', {'habit_id': 'h1', 'date': '2026-11-24', 'done': False},
                            updated_at=AGORA + 9)
        self.cliente.marcar_habito('Leitura')
        registro = self.servidor.registros['hl_h1_2026-11-24']
        self.assertTrue(registro['data']['done'])
        self.assertEqual(registro['updated_at'], AGORA + 10)

    def test_conflito_no_servidor_e_avisado(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Ler', 'done': False}, updated_at=1)
        original = self.servidor.post

        def post_com_corrida(url, **kw):
            if url.endswith('/rpc/sync_push'):
                self.servidor.registros['t1']['updated_at'] = AGORA * 2
            return original(url, **kw)

        self.servidor.post = post_com_corrida
        with self.assertRaisesRegex(life_os.ErroLifeOS, 'outro aparelho'):
            self.cliente.concluir_tarefa('Ler')

    # ---------- resumo ----------
    def test_resumo_do_dia(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Atrasada', 'due': '2026-11-20', 'done': False})
        self.servidor.criar('tasks', 't2', {'title': 'De hoje', 'due': '2026-11-24', 'done': False})
        self.servidor.criar('tasks', 't3', {'title': 'Feita hoje', 'due': '2026-11-24', 'done': True})
        self.servidor.criar('tasks', 't4', {'title': 'Futura', 'due': '2026-12-01', 'done': False})
        self.servidor.criar('habits', 'h1', {'name': 'Leitura', 'days': [2]})
        self.servidor.criar('habits', 'h2', {'name': 'Academia', 'days': [1, 3, 5]})
        self.servidor.criar('habits', 'h3', {'name': 'Água', 'days': []})
        self.servidor.criar('habit_logs', 'hl_h1_2026-11-24', {'habit_id': 'h1', 'date': '2026-11-24', 'done': True})
        resumo = self.cliente.resumo_hoje()
        self.assertIn('Atrasada', resumo)
        self.assertIn('De hoje', resumo)
        self.assertNotIn('Feita hoje', resumo)
        self.assertNotIn('Futura', resumo)
        self.assertNotIn('Academia', resumo)
        self.assertRegex(resumo, r'\[x\] Leitura')
        self.assertRegex(resumo, r'\[ \] Água')

    def test_lista_de_tarefas_agrupa_por_prazo(self):
        self.entrar()
        self.servidor.criar('tasks', 't1', {'title': 'Sem prazo', 'due': None, 'done': False})
        self.servidor.criar('tasks', 't2', {'title': 'Futura', 'due': '2026-12-01', 'done': False})
        texto = self.cliente.listar_tarefas()
        self.assertLess(texto.index('Futura'), texto.index('Sem prazo'))

    def test_servidor_fora_do_ar(self):
        self.entrar()

        def falha(*a, **kw):
            raise life_os.requests.ConnectionError('sem rede')

        self.servidor.get = falha
        with self.assertRaisesRegex(life_os.ErroLifeOS, 'conexão'):
            self.cliente.resumo_hoje()


class PedidoTestes(unittest.TestCase):
    def p(self, texto):
        return life_os.pedido(texto, hoje=HOJE)

    def test_comandos(self):
        self.assertEqual(self.p('/tarefa Estudar física amanhã'), ('tarefa', ('Estudar física', '2026-11-25')))
        self.assertEqual(self.p('/tarefa Pagar luz 05/12'), ('tarefa', ('Pagar luz', '2026-12-05')))
        self.assertEqual(self.p('/tarefa Prova 10/01/2027'), ('tarefa', ('Prova', '2027-01-10')))
        self.assertEqual(self.p('/tarefa Ler'), ('tarefa', ('Ler', None)))
        self.assertEqual(self.p('/tarefas'), ('tarefas', ()))
        self.assertEqual(self.p('/hoje'), ('hoje', ()))
        self.assertEqual(self.p('/feito Pagar luz'), ('feito', ('Pagar luz',)))
        self.assertEqual(self.p('/habito Leitura'), ('habito', ('Leitura',)))
        self.assertEqual(self.p('/hábito Leitura'), ('habito', ('Leitura',)))
        self.assertEqual(self.p('/lifeos'), ('status', ()))
        self.assertEqual(self.p('/lifeos sair'), ('sair', ()))
        self.assertEqual(self.p('/lifeos entrar'), ('entrar', ()))

    def test_data_do_ano_que_vem(self):
        self.assertEqual(self.p('/tarefa Viagem 02/01'), ('tarefa', ('Viagem', '2027-01-02')))

    def test_frases(self):
        self.assertEqual(self.p('Omega, cria a tarefa estudar física pra amanhã'),
                         ('tarefa', ('estudar física', '2026-11-25')))
        self.assertEqual(self.p('adiciona uma tarefa: comprar pão'), ('tarefa', ('comprar pão', None)))
        self.assertEqual(self.p('nova tarefa ligar para o dentista hoje'),
                         ('tarefa', ('ligar para o dentista', '2026-11-24')))
        self.assertEqual(self.p('o que eu tenho pra hoje?'), ('hoje', ()))
        self.assertEqual(self.p('Omega, como está meu dia?'), ('hoje', ()))
        self.assertEqual(self.p('quais são minhas tarefas'), ('tarefas', ()))
        self.assertEqual(self.p('terminei a tarefa pagar luz'), ('feito', ('pagar luz',)))
        self.assertEqual(self.p('conclui a tarefa Pagar luz.'), ('feito', ('Pagar luz',)))
        self.assertEqual(self.p('marquei o hábito de leitura'), ('habito', ('leitura',)))
        self.assertEqual(self.p('fiz o habito academia hoje'), ('habito', ('academia',)))

    def test_conversa_normal_nao_e_pedido(self):
        for texto in ['que horas são', 'me fale sobre tarefas de casa na história',
                      'qual o clima hoje', '/tarefa', 'o que é um hábito?']:
            self.assertIsNone(self.p(texto), texto)


if __name__ == '__main__':
    unittest.main()
