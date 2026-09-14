"""Entrada pt-BR online e leitura local, carregadas somente no modo de voz."""
import json
import subprocess
import sys
from pathlib import Path

PERFIS = {
    'Windows (offline)': None,
    'oproprio': ('pt-BR-AntonioNeural', '-3%', '-4Hz'),
    'daydiva': ('pt-BR-FranciscaNeural', '-3%', '+0Hz'),
}

class ErroVoz(Exception):
    pass


def ouvir():
    try:
        import speech_recognition as sr
        import sounddevice as sd
    except ImportError as exc:
        raise ErroVoz('Instale as dependências: python -m pip install -r requirements-voice.txt') from exc
    recognizer = sr.Recognizer()
    recognizer.operation_timeout = 15
    try:
        with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16') as source:
            blocos = [bytes(source.read(1600)[0]) for _ in range(80)]
        audio = sr.AudioData(b''.join(blocos), 16000, 2)
        return recognizer.recognize_google(audio, language='pt-BR')
    except sr.WaitTimeoutError as exc:
        raise ErroVoz('Não detectei fala. Clique no microfone para tentar novamente.') from exc
    except sr.UnknownValueError as exc:
        raise ErroVoz('Não entendi a fala. Tente novamente ou digite sua mensagem.') from exc
    except sr.RequestError as exc:
        raise ErroVoz('O reconhecimento online está indisponível. Confira sua conexão.') from exc
    except (OSError, AttributeError, sd.PortAudioError) as exc:
        raise ErroVoz('Microfone indisponível. Confira as permissões do Windows e as dependências de voz.') from exc


class Leitor:
    def __init__(self):
        self.processo = None
        self.perfil = 'Windows (offline)'

    def parar(self):
        if self.processo is not None:
            if self.processo.poll() is None:
                self.processo.terminate()
                self.processo.wait(timeout=3)
            self.processo = None

    def falar(self, texto):
        import importlib.util
        modulos = ['edge_tts', 'pygame'] if PERFIS[self.perfil] else ['pyttsx3']
        if any(importlib.util.find_spec(modulo) is None for modulo in modulos):
            raise ErroVoz('Instale as dependências: python -m pip install -r requirements-voice.txt')
        self.parar()
        self.processo = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--falar'],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            self.processo.stdin.write(json.dumps({'texto': texto, 'perfil': self.perfil}).encode('utf-8'))
            self.processo.stdin.close()
        except OSError as exc:
            self.parar()
            raise ErroVoz('Não consegui iniciar a leitura da resposta.') from exc


def sintetizar(texto):
    import pyttsx3
    engine = pyttsx3.init()
    for voz in engine.getProperty('voices'):
        descricao = (str(voz.id) + str(voz.name) + str(voz.languages)).lower()
        if any(p in descricao for p in ('brazil', 'portugu', 'pt-br', '0416')):
            engine.setProperty('voice', voz.id)
            break
    engine.setProperty('rate', 175)
    engine.say(texto)
    engine.runAndWait()
    engine.stop()

async def gerar_neural(texto, perfil):
    import edge_tts
    voz, ritmo, tom = PERFIS[perfil]
    comunicacao = edge_tts.Communicate(texto, voz, rate=ritmo, pitch=tom,
                                      connect_timeout=10, receive_timeout=30)
    audio = bytearray()
    async for parte in comunicacao.stream():
        if parte['type'] == 'audio':
            audio.extend(parte['data'])
    if not audio:
        raise ErroVoz('O serviço de voz não retornou áudio.')
    return bytes(audio)


def sintetizar_neural(texto, perfil):
    import asyncio
    import io
    import time
    import pygame
    dados = asyncio.run(asyncio.wait_for(gerar_neural(texto, perfil), timeout=90))
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(io.BytesIO(dados), 'mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(.05)
    finally:
        pygame.mixer.quit()


if __name__ == '__main__' and '--falar' in sys.argv:
    pedido = json.loads(sys.stdin.buffer.read().decode('utf-8'))
    if PERFIS[pedido['perfil']]:
        sintetizar_neural(pedido['texto'], pedido['perfil'])
    else:
        sintetizar(pedido['texto'])
