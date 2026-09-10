import unittest
from pathlib import Path
from unittest.mock import patch
import computer
import main
from functions import ErroServico

class ComputerTests(unittest.TestCase):
    def test_requests(self):
        for text, expected in [('abra a calculadora', 'calculadora'), ('Omega, pode abrir o Chrome?', 'chrome'),
                               ('/abrir VS Code', 'vs code'), ('abre o paint por favor', 'paint'),
                               ('/abrir', ''), ('como abrir o chrome?', None),
                               ('não abra a calculadora', None)]:
            with self.subTest(text=text):
                self.assertEqual(computer.pedido_abertura(text), expected)

    def test_action_bypasses_model(self):
        with patch('computer.abrir_app', return_value='aberto') as launch, patch('main.ollama_brain.analisar_pergunta') as model:
            self.assertEqual(main.responder('abra a calculadora', [], interativo=False), 'aberto')
            launch.assert_called_once_with('calculadora')
            model.assert_not_called()

    def test_try_open_paint_bypasses_model(self):
        for text in ['tente abrir o paint', 'tenta abrir o paint',
                     'você consegue abrir o Paint?', 'quero que você abra o paint']:
            with self.subTest(text=text), patch('computer.abrir_app', return_value='Solicitado') as launch, patch('main.ollama_brain.analisar_pergunta') as model:
                self.assertEqual(main.responder(text, [], interativo=False), 'Solicitado')
                launch.assert_called_once_with('paint')
                model.assert_not_called()

    def test_negated_and_hypothetical_requests_do_not_open(self):
        for text in ['não tente abrir o paint', 'se eu pedir, você consegue abrir o paint?',
                     'ele disse tente abrir o paint']:
            self.assertIsNone(computer.pedido_abertura(text))

    def test_rejects_commands_and_arguments(self):
        for value in ['cmd', 'powershell', 'chrome & calc', 'calc.exe', 'chrome --incognito', 'C:/app.exe']:
            with self.subTest(value=value), patch('computer.subprocess.Popen') as launch:
                with self.assertRaises(ErroServico):
                    computer.abrir_app(value)
                launch.assert_not_called()

    def test_launch_without_shell(self):
        with patch('computer.localizar_app', return_value=Path('C:/Windows/System32/calc.exe')), patch('computer.subprocess.Popen') as launch:
            self.assertIn('Calculadora', computer.abrir_app('calc'))
            self.assertFalse(launch.call_args.kwargs['shell'])
            self.assertEqual(len(launch.call_args.args[0]), 1)

    def test_missing_installation(self):
        with patch('computer.localizar_app', return_value=None), self.assertRaises(ErroServico):
            computer.abrir_app('spotify')

    def test_launch_failure(self):
        with patch('computer.localizar_app', return_value=Path('C:/Windows/System32/calc.exe')), patch('computer.subprocess.Popen', side_effect=OSError), self.assertRaises(ErroServico):
            computer.abrir_app('calc')

if __name__ == '__main__':
    unittest.main()
