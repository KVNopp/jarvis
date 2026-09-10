"""Interface desktop do Omega. Execute: python interface.py."""
import queue
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

from config import MODELO
from main import AJUDA, CidadeNecessaria, responder
from memory import ErroMemoria, carregar_memoria, salvar_memoria
from visualizer import AnelOmega

BG = '#08060d'
PANEL = '#100b18'
TEXT = '#f1eafa'
MUTED = '#ad9bbb'
ACCENT = '#c084fc'


class OmegaApp:
    def __init__(self, root):
        self.root = root
        self.fila = queue.Queue()
        self.ocupado = False
        self.pergunta = ''
        self.memoria = carregar_memoria()
        root.title('Omega | Assistente pessoal')
        root.geometry('1060x760')
        root.minsize(760, 700)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.fechar)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        lateral = tk.Frame(root, bg=PANEL, width=220, padx=22, pady=28)
        lateral.grid(row=0, column=0, sticky='nsew')
        lateral.grid_propagate(False)
        self.label(lateral, 'O M E G A', 23, ACCENT).pack(anchor='w')
        self.label(lateral, 'Seu assistente pessoal', 10, MUTED).pack(anchor='w', pady=(6, 4))
        self.anel = AnelOmega(lateral, fundo=PANEL)
        self.anel.pack(fill='x', pady=(0, 2))
        self.animacao_botao = tk.Button(lateral, text='Pausar animação', command=self.alternar_animacao,
                                       bg=PANEL, fg=MUTED, activebackground=PANEL,
                                       activeforeground=ACCENT, relief='flat', cursor='hand2')
        self.animacao_botao.pack(pady=(0, 12))
        self.label(lateral, 'ATALHOS', 9, MUTED).pack(anchor='w', pady=(0, 12))
        self.atalhos = []
        for titulo, comando in [('Hora atual', '/hora'), ('Data de hoje', '/data'),
                                ('Consultar clima', '/clima '), ('Pesquisar na web', '/buscar ')]:
            botao = self.botao(lateral, titulo, lambda c=comando: self.preencher(c))
            botao.pack(fill='x', pady=5)
            self.atalhos.append(botao)
        self.botao(lateral, 'Ajuda e comandos', self.ajuda).pack(fill='x', pady=(24, 5))
        self.contagem = self.label(lateral, '', 10, MUTED)
        self.contagem.pack(side='bottom', anchor='w', pady=8)
        self.label(lateral, f'Modelo: {MODELO}', 10, MUTED).pack(side='bottom', anchor='w')

        principal = tk.Frame(root, bg=BG, padx=28, pady=24)
        principal.grid(row=0, column=1, sticky='nsew')
        principal.grid_columnconfigure(0, weight=1)
        principal.grid_rowconfigure(2, weight=1)
        self.label(principal, 'Vamos conversar.', 24, TEXT, BG).grid(row=0, column=0, sticky='w')
        self.label(principal, 'Ideias, dúvidas e tarefas do dia a dia.', 11, MUTED, BG).grid(row=1, column=0, sticky='w', pady=(6, 20))
        self.chat = ScrolledText(principal, wrap='word', bg=BG, fg=TEXT, relief='flat',
                                 font=('Segoe UI', 11), padx=16, pady=16,
                                 insertbackground=TEXT, selectbackground='#532875', state='disabled')
        self.chat.grid(row=2, column=0, sticky='nsew')
        self.chat.tag_configure('user', foreground=ACCENT, font=('Segoe UI', 10, 'bold'), spacing1=16, spacing3=6)
        self.chat.tag_configure('assistant', foreground='#d9b3ff', font=('Segoe UI', 10, 'bold'), spacing1=16, spacing3=6)
        self.chat.tag_configure('info', foreground=MUTED, spacing1=12, spacing3=10)
        self.chat.tag_configure('body', spacing3=18)
        self.status = tk.StringVar(value='Pronto para conversar')
        tk.Label(principal, textvariable=self.status, bg=BG, fg=ACCENT, anchor='w', font=('Segoe UI', 10)).grid(row=3, column=0, sticky='ew', pady=10)

        compositor = tk.Frame(principal, bg=PANEL, padx=12, pady=12)
        compositor.grid(row=4, column=0, sticky='ew')
        compositor.grid_columnconfigure(0, weight=1)
        self.entrada = tk.Text(compositor, height=3, wrap='word', bg=PANEL, fg=TEXT,
                               insertbackground=TEXT, relief='flat', font=('Segoe UI', 11))
        self.entrada.grid(row=0, column=0, sticky='ew', padx=(0, 12))
        self.entrada.bind('<Return>', self.enter)
        self.enviar_botao = self.botao(compositor, 'Enviar  →', self.enviar, destaque=True)
        self.enviar_botao.grid(row=0, column=1, sticky='se')
        self.label(principal, 'Enter para enviar · Shift + Enter para uma nova linha', 9, MUTED, BG).grid(row=5, column=0, sticky='w', pady=(10, 0))
        visiveis = [m for m in self.memoria if m['role'] != 'system']
        if len(visiveis) > 60:
            self.mensagem('info', 'Mostrando as 60 mensagens mais recentes. O histórico completo continua salvo.')
        for item in visiveis[-60:]:
            self.mensagem(item['role'], item['content'])
        if not visiveis:
            self.mensagem('assistant', 'Olá! Sou o Omega. Como posso ajudar hoje?')
        self.atualizar_contagem()
        self.entrada.focus_set()
        self.timer = root.after(100, self.processar_fila)
        root.bind('<Destroy>', self.cancelar_timer, add='+')

    def cancelar_timer(self, event):
        if event.widget is self.root:
            self.root.after_cancel(self.timer)

    def label(self, parent, texto, tamanho, cor, fundo=PANEL):
        return tk.Label(parent, text=texto, bg=fundo, fg=cor, font=('Segoe UI', tamanho), anchor='w')

    def botao(self, parent, texto, comando, destaque=False):
        return tk.Button(parent, text=texto, command=comando, bg=ACCENT if destaque else '#261536',
                         fg=BG if destaque else TEXT, activebackground='#dfb5ff', activeforeground=BG,
                         relief='flat', borderwidth=0, padx=12, pady=10, cursor='hand2', font=('Segoe UI', 10))

    def mensagem(self, papel, texto):
        self.chat.configure(state='normal')
        if papel == 'info':
            self.chat.insert('end', texto + '\n', 'info')
        else:
            self.chat.insert('end', ('VOCÊ' if papel == 'user' else 'OMEGA') + '\n', papel)
            self.chat.insert('end', texto + '\n', 'body')
        self.chat.configure(state='disabled')
        self.chat.see('end')

    def atualizar_contagem(self):
        self.contagem.configure(text=f'{len(self.memoria)} registros salvos')

    def preencher(self, comando):
        if not self.ocupado:
            self.entrada.delete('1.0', 'end')
            self.entrada.insert('1.0', comando)
            self.entrada.focus_set()

    def ajuda(self):
        messagebox.showinfo('Como usar o Omega', AJUDA, parent=self.root)

    def enter(self, event):
        if event.state & 1:
            return None
        self.enviar()
        return 'break'

    def definir_ocupado(self, valor):
        self.ocupado = valor
        self.anel.ativo = valor
        estado = 'disabled' if valor else 'normal'
        self.enviar_botao.configure(state=estado)
        for botao in self.atalhos:
            botao.configure(state=estado)
        self.status.set('Omega pensando...' if valor else 'Pronto para conversar')

    def alternar_animacao(self):
        pausado = self.anel.alternar()
        self.animacao_botao.configure(text='Retomar animação' if pausado else 'Pausar animação')

    def enviar(self):
        if self.ocupado:
            return
        pergunta = self.entrada.get('1.0', 'end').strip()
        if not pergunta:
            return
        if pergunta.lower() in {'/sair', 'sair', 'exit', 'quit'}:
            self.fechar()
            return
        if pergunta.lower() in {'/ajuda', '/memoria'}:
            if pergunta.lower() == '/ajuda':
                self.ajuda()
            else:
                messagebox.showinfo('Memória', f'{len(self.memoria)} registros salvos.', parent=self.root)
            self.entrada.delete('1.0', 'end')
            return
        if pergunta.startswith('/') and pergunta.split()[0].lower() not in {'/hora', '/data', '/clima', '/buscar', '/abrir', '/apps'}:
            self.mensagem('info', 'Comando desconhecido. Consulte Ajuda e comandos.')
            return
        self.pergunta = pergunta
        self.entrada.delete('1.0', 'end')
        self.mensagem('user', pergunta)
        self.definir_ocupado(True)
        self.iniciar_consulta(pergunta)

    def iniciar_consulta(self, pergunta):
        # A thread não acessa widgets; a fila devolve resultados à thread do Tk.
        historico = list(self.memoria)
        threading.Thread(target=self.trabalhar, args=(pergunta, historico), daemon=True).start()

    def trabalhar(self, pergunta, historico):
        try:
            resposta = responder(pergunta, historico, interativo=False)
            self.fila.put(('resposta', resposta))
        except CidadeNecessaria:
            self.fila.put(('cidade', None))
        except Exception as exc:
            self.fila.put(('erro', str(exc)))

    def processar_fila(self):
        try:
            tipo, valor = self.fila.get_nowait()
        except queue.Empty:
            self.timer = self.root.after(100, self.processar_fila)
            return
        if tipo == 'cidade':
            self.status.set('Aguardando cidade')
            cidade = simpledialog.askstring('Consultar clima', 'De qual cidade?', parent=self.root)
            if cidade and cidade.strip():
                self.status.set('Consultando o clima...')
                self.iniciar_consulta('/clima ' + cidade.strip())
            else:
                self.mensagem('info', 'Consulta cancelada. Nenhuma mensagem foi salva.')
                self.definir_ocupado(False)
        elif tipo == 'resposta':
            self.mensagem('assistant', valor)
            nova = self.memoria + [{'role': 'user', 'content': self.pergunta}, {'role': 'assistant', 'content': valor}]
            try:
                salvar_memoria(nova)
            except ErroMemoria as exc:
                self.mensagem('info', f'{exc} Esta interação não foi salva.')
            else:
                self.memoria = nova
                self.atualizar_contagem()
            self.definir_ocupado(False)
        else:
            self.mensagem('info', f'Não foi possível responder: {valor}\nVocê pode tentar novamente.')
            self.definir_ocupado(False)
        self.timer = self.root.after(100, self.processar_fila)

    def fechar(self):
        if self.ocupado and not messagebox.askyesno('Encerrar Omega', 'Há uma resposta em andamento. Sair sem salvá-la?', parent=self.root):
            return
        self.root.destroy()


def executar():
    root = tk.Tk()
    try:
        OmegaApp(root)
    except ErroMemoria as exc:
        root.withdraw()
        messagebox.showerror('Não foi possível abrir a memória', str(exc), parent=root)
        root.destroy()
        return 1
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(executar())
