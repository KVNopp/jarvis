import contextlib
import io
import unittest
from unittest.mock import patch

import life_os
import main


class MainLifeOSTestes(unittest.TestCase):
    def test_pedido_do_life_os_nao_passa_pela_ia(self):
        with patch('main.life_os.executar', return_value='Tarefa criada') as executar, \
                patch('main.ollama_brain.analisar_pergunta') as ia:
            self.assertEqual(main.responder('Omega, cria a tarefa comprar pão', []), 'Tarefa criada')
        executar.assert_called_once_with('tarefa', ('comprar pão', None))
        ia.assert_not_called()

    def test_comandos_do_life_os_sao_conhecidos(self):
        for comando in ['/tarefa Ler', '/tarefas', '/hoje', '/feito Ler', '/habito Leitura', '/lifeos', '/lifeos sair']:
            self.assertTrue(main.comando_conhecido(comando), comando)
        for comando in ['/xyz', '/tarefa', '/lifeos qualquer']:
            self.assertFalse(main.comando_conhecido(comando), comando)
        self.assertTrue(main.comando_conhecido('/clima Recife'))
        self.assertTrue(main.comando_conhecido('texto sem barra'))

    def test_login_pelo_terminal(self):
        saida = io.StringIO()
        with patch('main.life_os.entrar_interativo', return_value='Conectado ao LIFE OS como eu@x.com.') as entrar, \
                patch('main.carregar_memoria') as memoria, contextlib.redirect_stdout(saida):
            self.assertEqual(main.executar_argumentos(['/lifeos', 'entrar']), 0)
        entrar.assert_called_once()
        memoria.assert_not_called()
        self.assertIn('Conectado', saida.getvalue())

    def test_erro_do_life_os_e_mostrado(self):
        saida = io.StringIO()
        with patch('main.life_os.executar', side_effect=life_os.ErroLifeOS('Entre primeiro')), \
                patch('main.carregar_memoria', return_value=[]), patch('main.salvar_memoria') as salvar, \
                contextlib.redirect_stdout(saida):
            self.assertEqual(main.executar_argumentos(['/hoje']), 1)
        self.assertIn('Entre primeiro', saida.getvalue())
        salvar.assert_not_called()

    def test_ajuda_cita_os_comandos(self):
        for comando in ['/tarefa', '/tarefas', '/hoje', '/feito', '/habito', '/lifeos']:
            self.assertIn(comando, main.AJUDA)


if __name__ == '__main__':
    unittest.main()
