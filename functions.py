"""Consultas externas com limites de espera e erros recuperáveis."""
import os
import time
import requests
from duckduckgo_search import DDGS
from memory import carregar_memoria, salvar_memoria

class ErroServico(Exception):
    pass

def obter_clima(cidade):
    chave = os.getenv('OPENWEATHER_API_KEY', '').strip()
    if not chave:
        raise ErroServico('Configure OPENWEATHER_API_KEY no arquivo .env para consultar o clima.')
    try:
        resposta = requests.get('https://api.openweathermap.org/data/2.5/weather',
            params={'q': cidade, 'appid': chave, 'units': 'metric', 'lang': 'pt_br'}, timeout=(5, 15))
        if resposta.status_code == 404:
            raise ErroServico('Cidade não encontrada. Tente incluir o país, por exemplo: São Paulo,BR.')
        if resposta.status_code == 401:
            raise ErroServico('A chave de clima não foi aceita. Confira OPENWEATHER_API_KEY no .env.')
        resposta.raise_for_status()
        dados = resposta.json()
        return f"O clima em {dados.get('name', cidade)} está em {dados['main']['temp']}°C com {dados['weather'][0]['description']}."
    except requests.Timeout as exc:
        raise ErroServico('A consulta de clima demorou demais. Tente novamente.') from exc
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise ErroServico('Não consegui consultar o clima agora. Tente novamente mais tarde.') from exc

def buscar_na_web(pergunta):
    try:
        with DDGS(timeout=15) as ddgs:
            resultados = list(ddgs.text(pergunta, max_results=3))
        fontes = [{'title': str(r.get('title', 'Fonte'))[:200],
                   'href': str(r.get('href', '')), 'body': str(r.get('body', ''))[:2500]}
                  for r in resultados if str(r.get('href', '')).startswith(('https://', 'http://'))]
        if not fontes:
            raise ErroServico('Não encontrei resultados. Tente uma busca mais específica.')
        return fontes
    except ErroServico:
        raise
    except Exception as exc:
        raise ErroServico('A busca web está indisponível. Tente novamente mais tarde.') from exc

def calculadora():
    print("Calculadora iniciada.")
    time.sleep(1)
    print("========== calculadora ==========")
    try:
        num1 = float(input('Escolha um número: '))
        num2 = float(input('Escolha outro número: '))

        adicao = num1 + num2
        subtracao = num1 - num2
        multiplicacao = num1 * num2
        divisao = num1 / num2 if num2 != 0 else "Erro: Divisão por zero!"

        print('\nOperações realizadas:')
        print(f'1 - Adição: {adicao}')
        print(f'2 - Subtração: {subtracao}')
        print(f'3 - Multiplicação: {multiplicacao}')
        print(f'4 - Divisão: {divisao}')
    except ValueError:
        print("Erro: Por favor, digite apenas números.")

def obter_data():
    data_atual = time.localtime()
    return f"{data_atual.tm_mday:02d}/{data_atual.tm_mon:02d}/{data_atual.tm_year}"

def obter_hora():
    hora_atual = time.localtime()
    return f"{hora_atual.tm_hour:02d}:{hora_atual.tm_min:02d}:{hora_atual.tm_sec:02d}"
