import time
import json






def salvar_memoria(memoria, nome_arquivo="memoria.json"):
    with open(nome_arquivo, 'w') as arquivo:
        json.dump(memoria, arquivo)

def carregar_memoria(nome_arquivo="memoria.json"):
    try:
        with open(nome_arquivo, 'r') as arquivo:
            memoria = json.load(arquivo)
    except FileNotFoundError:
        memoria = []
    return memoria

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
