import contextlib
import io
import subprocess
import unittest
from unittest.mock import patch, Mock

import main
import pc_remoto
from brain import ollama_brain


class ControlePCTest(unittest.TestCase):
    def test_pedidos_explicitos(self):
        for texto, acao in [('Omega, liga o PC!', 'ligar'), ('ligar pc', 'ligar'),
                            ('/desligar', 'desligar'), ('desligue meu computador por favor', 'desligar')]:
            self.assertEqual(pc_remoto.pedido_energia(texto), acao)

    def test_nao_executa_negacoes_citacoes_ou_comandos_extras(self):
        for texto in ['não desligue o pc', 'como desligar pc?', 'ele disse desligar pc',
                      'desligar pc & calc', 'ligar pc amanhã', 'se eu pedir, desligue o pc',
                      '"desligar pc"', '/desligar agora']:
            self.assertIsNone(pc_remoto.pedido_energia(texto), texto)

    def test_pacote_wol(self):
        with patch.dict('os.environ', {}, clear=True), patch('pc_remoto.socket.socket') as sock:
            pc_remoto.executar('ligar')
            dados, destino = sock.return_value.__enter__.return_value.sendto.call_args.args
            self.assertEqual(dados, b'\xff' * 6 + bytes.fromhex('74563CB40C65') * 16)
            self.assertEqual(destino, ('192.168.15.255', 9))

    def test_mac_invalido_nao_envia(self):
        with patch.dict('os.environ', {'PC_MAC': '00'}), patch('pc_remoto.socket.socket') as sock:
            with self.assertRaises(pc_remoto.ErroPC):
                pc_remoto.executar('ligar')
            sock.assert_not_called()

    def test_ssh_sem_shell_senha_ou_forcar_aplicativos(self):
        with patch('pc_remoto.Path.is_file', return_value=True), patch('pc_remoto.subprocess.run', return_value=Mock(returncode=0)) as run:
            self.assertIn('enviado', pc_remoto.executar('desligar'))
            comando = run.call_args.args[0]
            self.assertEqual(comando[-1], 'shutdown.exe /s /t 0')
            self.assertIn('BatchMode=yes', comando)
            self.assertFalse(run.call_args.kwargs['shell'])

    def test_erro_ssh_nao_reporta_sucesso(self):
        with patch('pc_remoto.Path.is_file', return_value=True), patch('pc_remoto.subprocess.run', return_value=Mock(returncode=255, stderr='Permission denied', stdout='')):
            with self.assertRaisesRegex(pc_remoto.ErroPC, 'Permission denied'):
                pc_remoto.executar('desligar')

    def test_timeout_e_chave_ausente(self):
        with patch('pc_remoto.Path.is_file', return_value=False), patch('pc_remoto.subprocess.run') as run:
            with self.assertRaises(pc_remoto.ErroPC):
                pc_remoto.executar('desligar')
            run.assert_not_called()
        with patch('pc_remoto.Path.is_file', return_value=True), patch('pc_remoto.subprocess.run', side_effect=subprocess.TimeoutExpired('ssh', 20)):
            with self.assertRaises(pc_remoto.ErroPC):
                pc_remoto.executar('desligar')

    def test_controle_ignora_ia_e_historico(self):
        with patch('pc_remoto.executar', return_value='enviado') as action, patch.object(ollama_brain, 'analisar_pergunta', side_effect=AssertionError):
            self.assertEqual(main.responder('ligar pc', [{'role': 'user', 'content': 'desligar pc'}]), 'enviado')
            action.assert_called_once_with('ligar')

    def test_cli_independe_da_memoria(self):
        with patch('pc_remoto.executar', return_value='enviado'), patch('main.carregar_memoria', side_effect=AssertionError), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.executar_argumentos(['ligar', 'pc']), 0)
        with patch('pc_remoto.executar', side_effect=pc_remoto.ErroPC('erro')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.executar_argumentos(['/desligar']), 1)

    def test_api_ollama_preserva_schema_e_timeout(self):
        resposta = Mock()
        resposta.json.return_value = {'message': {'content': 'resposta'}}
        with patch.object(ollama_brain.requests, 'post', return_value=resposta) as post:
            self.assertEqual(ollama_brain._chat([], estruturado=True), 'resposta')
            self.assertTrue(post.call_args.args[0].endswith('/api/chat'))
            self.assertFalse(post.call_args.kwargs['json']['stream'])
            self.assertIn('format', post.call_args.kwargs['json'])
            self.assertEqual(post.call_args.kwargs['timeout'], (5, 120))
