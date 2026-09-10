import time
import tkinter as tk
import unittest
from unittest.mock import patch
import interface


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        with patch('interface.carregar_memoria', return_value=[]):
            self.app = interface.OmegaApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def esperar(self):
        limite = time.monotonic() + 3
        while self.app.ocupado and time.monotonic() < limite:
            self.root.update()
            time.sleep(.01)
        self.assertFalse(self.app.ocupado)

    def test_send_and_save(self):
        with patch('interface.responder', return_value='Olá!') as reply, patch('interface.salvar_memoria') as save:
            self.app.entrada.insert('1.0', 'Oi')
            self.app.enviar()
            self.esperar()
            reply.assert_called_once_with('Oi', [], interativo=False)
            self.assertEqual(len(save.call_args.args[0]), 2)
            self.assertEqual(self.app.status.get(), 'Pronto para conversar')
            self.assertIn('Olá!', self.app.chat.get('1.0', 'end'))

    def test_city_dialog(self):
        with patch('interface.responder', side_effect=[interface.CidadeNecessaria(), 'Sol']) as reply, patch('interface.simpledialog.askstring', return_value='Recife'), patch('interface.salvar_memoria'):
            self.app.entrada.insert('1.0', '/clima')
            self.app.enviar()
            self.esperar()
            self.assertEqual(reply.call_args.args[0], '/clima Recife')

    def test_error_not_saved(self):
        with patch('interface.responder', side_effect=RuntimeError('offline')), patch('interface.salvar_memoria') as save:
            self.app.entrada.insert('1.0', 'Oi')
            self.app.enviar()
            self.esperar()
            save.assert_not_called()
            self.assertIn('offline', self.app.chat.get('1.0', 'end'))

    def test_empty_input(self):
        with patch('interface.responder') as reply:
            self.app.enviar()
            reply.assert_not_called()


if __name__ == '__main__':
    unittest.main()
