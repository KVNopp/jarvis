"""Anel procedural inspirado em visualizadores musicais; não usa áudio ou GIF."""
import math
import time
import tkinter as tk


class AnelOmega(tk.Canvas):
    def __init__(self, parent, fundo='#0b080f'):
        super().__init__(parent, width=170, height=150, bg=fundo, highlightthickness=0)
        self.ativo = False
        self.pausado = False
        self.timer = None
        self.inicio = time.monotonic()
        self.linhas = [self.create_line(0, 0, 1, 1, fill=cor, width=largura,
                                       smooth=True, splinesteps=8)
                       for cor, largura in [('#21102f', 16), ('#3d165c', 10),
                                             ('#762db0', 5), ('#c678ff', 2)]]
        self.create_oval(49, 39, 121, 111, outline='#39204e', width=1)
        self.create_text(85, 72, text='Ω', fill='#e5c4ff', font=('Segoe UI', 28))
        self.create_text(85, 101, text='O M E G A', fill='#9f75b9', font=('Segoe UI', 7))
        self.bind('<Destroy>', self.encerrar, add='+')
        self.animar()

    def animar(self):
        self.timer = None
        if self.pausado:
            return
        t = time.monotonic() - self.inicio
        amplitude = 7 if self.ativo else 2.5
        fase = t * (3.8 if self.ativo else 1.2)
        pontos = []
        for i in range(121):
            angulo = math.tau * i / 120
            onda = (math.sin(angulo * 7 + fase) + .5 * math.sin(angulo * 13 - fase * 1.3)
                    + .3 * math.sin(angulo * 23 + fase * .7))
            raio = 52 + math.sin(fase) * 1.5 + amplitude * onda
            pontos.extend((85 + math.cos(angulo) * raio, 75 + math.sin(angulo) * raio))
        for linha in self.linhas:
            self.coords(linha, *pontos)
        self.timer = self.after(33, self.animar)

    def alternar(self):
        self.pausado = not self.pausado
        if self.pausado and self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
        elif not self.pausado:
            self.animar()
        return self.pausado

    def encerrar(self, event):
        if event.widget is self and self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
