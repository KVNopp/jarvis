import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import requests
import main
import memory
import functions
from brain import ollama_brain as brain

class OmegaTests(unittest.TestCase):
    def test_roundtrip_and_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'memoria.json'
            original = [{'role': 'user', 'content': 'Preferência: café'}]
            memory.salvar_memoria(original, path)
            memory.salvar_memoria(original + [{'role': 'assistant', 'content': 'Entendido'}], path)
            self.assertEqual(memory.carregar_memoria(path)[:1], original)
            self.assertEqual(memory.carregar_memoria(path.with_suffix('.json.bak')), original)

    def test_corrupt_memory_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'memoria.json'
            path.write_text('{incompleto', encoding='utf-8')
            with self.assertRaises(memory.ErroMemoria):
                memory.salvar_memoria([], path)
            self.assertEqual(path.read_text(), '{incompleto')

    def test_failed_replace_preserves_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'memoria.json'
            path.write_text('[]')
            with patch('memory.os.replace', side_effect=OSError), self.assertRaises(memory.ErroMemoria):
                memory.salvar_memoria([{'role': 'user', 'content': 'oi'}], path)
            self.assertEqual(path.read_text(), '[]')

    def test_context_recovers_old_memory_without_mutation(self):
        history = [{'role': 'user', 'content': 'Meu cachorro se chama Pipoca'}]
        history += [{'role': 'user', 'content': 'mensagem recente'} for _ in range(30)]
        before = json.dumps(history)
        result = memory.montar_contexto(history, 'Qual o nome do cachorro?')
        self.assertIn('Pipoca', json.dumps(result))
        self.assertEqual(json.dumps(history), before)

    def test_invalid_routes(self):
        for raw in ['[]', '{}', 'invalido', '{"intencao":"OUTRA"}', '{"intencao":"WEB","consulta":42}']:
            with self.subTest(raw=raw), patch.object(brain, '_chat', return_value=raw):
                self.assertEqual(brain.analisar_pergunta('oi'), ('CONVERSA', ''))

    def test_weather_city_extracted(self):
        with patch.object(brain, 'analisar_pergunta', return_value=('CLIMA', 'Recife')), patch.object(functions, 'obter_clima', return_value='sol') as weather:
            self.assertEqual(main.responder('Como está o clima em Recife?', []), 'sol')
            weather.assert_called_once_with('Recife')

    def test_clock_misclassification_does_not_override_conversation(self):
        history = [{'role': 'user', 'content': 'que horas sao?'},
                   {'role': 'assistant', 'content': 'Agora são 00:06:04.'}]
        for question in ['ola omega', 'como esta?', 'explique Python', 'o que é uma hora extra?']:
            for route in ['HORA', 'DATA']:
                with self.subTest(question=question, route=route), patch.object(
                    brain, '_chat', return_value=json.dumps({'intencao': route, 'consulta': ''})
                ), patch.object(brain, 'perguntar', return_value='Resposta de conversa') as answer:
                    self.assertEqual(main.responder(question, history), 'Resposta de conversa')
                    answer.assert_called_once_with(question, history)

    def test_explicit_clock_requests_do_not_need_model(self):
        with patch.object(brain, '_chat', side_effect=AssertionError('Não usar IA')):
            self.assertEqual(brain.analisar_pergunta('Omega, que horas são agora?'), ('HORA', ''))
            self.assertEqual(brain.analisar_pergunta('Qual é a data de hoje?'), ('DATA', ''))

    def test_router_separates_current_question_from_history(self):
        history = [{'role': 'user', 'content': 'clima em Recife'},
                   {'role': 'assistant', 'content': 'Resposta antiga incorreta'}]
        with patch.object(brain, '_chat', return_value='{"intencao":"CLIMA","consulta":"Natal"}') as chat:
            self.assertEqual(brain.analisar_pergunta('e em Natal?', history), ('CLIMA', 'Natal'))
            messages = chat.call_args.args[0]
            self.assertEqual([m['role'] for m in messages], ['system', 'user'])
            payload = json.loads(messages[-1]['content'])
            self.assertEqual(payload['pergunta_atual'], 'e em Natal?')
            self.assertEqual(payload['perguntas_anteriores'], ['clima em Recife'])

    def test_offline_commands(self):
        with patch.object(brain, '_chat', side_effect=AssertionError('Não usar IA')):
            self.assertIn('Agora', main.responder('/hora', []))
            self.assertIn('Hoje', main.responder('/data', []))

    def test_weather_timeout(self):
        with patch.dict('os.environ', {'OPENWEATHER_API_KEY': 'teste'}), patch('functions.requests.get', side_effect=requests.Timeout) as get:
            with self.assertRaises(functions.ErroServico):
                functions.obter_clima('Recife')
            self.assertTrue(get.call_args.args[0].startswith('https://'))
            self.assertIn('timeout', get.call_args.kwargs)

    def test_single_pair_saved_without_login(self):
        with patch('builtins.input', side_effect=['oi', '/sair']), patch.object(main, 'carregar_memoria', return_value=[]), patch.object(main, 'salvar_memoria') as save, patch.object(main, 'responder', return_value='Olá'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.executar(), 0)
            self.assertEqual(save.call_args.args[0], [{'role': 'user', 'content': 'oi'}, {'role': 'assistant', 'content': 'Olá'}])

    def test_service_error_not_saved(self):
        with patch('builtins.input', side_effect=['oi', '/sair']), patch.object(main, 'carregar_memoria', return_value=[]), patch.object(main, 'salvar_memoria') as save, patch.object(main, 'responder', side_effect=brain.ErroIA('offline')), contextlib.redirect_stdout(io.StringIO()):
            main.executar()
            save.assert_not_called()

    def test_web_sources_passed_and_displayed(self):
        sources = [{'title': 'Exemplo', 'href': 'https://example.com', 'body': 'texto'}]
        with patch.object(functions, 'buscar_na_web', return_value=sources), patch.object(brain, 'perguntar', return_value='Resposta') as ask, contextlib.redirect_stdout(io.StringIO()):
            self.assertIn('https://example.com', main.responder('/buscar teste', []))
            self.assertEqual(ask.call_args.kwargs['contexto_web'], sources)

if __name__ == '__main__':
    unittest.main()
