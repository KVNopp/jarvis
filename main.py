import time
import functions
from brain import ollama_brain

def iniciar_sistema():
    print("--- Inicializando Jarvis ---")
    nome = input("Digite seu nome: ")
    try:
        idade = int(input("Digite sua idade: "))
    except ValueError:
        print("Idade inválida. Definindo como 0.")
        idade = 0

    if idade < 18:
        print("Você é menor de idade.")
    else:
        print("Você é maior de idade.")

    senha_correta = 777
    while True:
        try:
            tentativa = int(input("Digite a senha para continuar: "))
            if tentativa == senha_correta:
                print("Senha correta! Acesso concedido.")
                break
            else:
                print("Senha incorreta! Tente novamente.")
                time.sleep(1)
        except ValueError:
            print("Por favor, digite a senha em números.")

    print(f"\nOlá, {nome}! Bem-vindo(a) ao programa. Eu sou o Jarvis.")
    return nome, idade

def menu():
    print('\n' + '='*30)
    print(' Como posso ajudar você?')
    print('='*30)
    print('1 - Saber a hora atual')
    print('2 - Saber a data atual')
    print('3 - Saber sua idade em dias')
    print('4 - Iniciar a calculadora')
    print('5 - Conversar com Jarvis (IA)')
    print('0 - Sair')
    print('='*30)

def script(nome, idade):
    try:
        opcao = int(input("Digite a opção desejada: "))

        if opcao == 1:
            hora = time.localtime()
            print(f"Hora atual: {hora.tm_hour:02d}:{hora.tm_min:02d}:{hora.tm_sec:02d}")

        elif opcao == 2:
            data = time.localtime()
            print(f"Data atual: {data.tm_mday:02d}/{data.tm_mon:02d}/{data.tm_year}")

        elif opcao == 3:
            idade_dias = idade * 365
            print(f"Sua idade aproximada em dias é: {idade_dias} dias")

        elif opcao == 4:
            functions.calculadora()

        elif opcao == 5:
            print("\n--- Modo de Conversa Ativado (Digite 'sair' para voltar ao menu) ---")
            while True:
                pergunta = input(f"{nome}: ")
                if pergunta.lower() in ['sair', 'exit', 'quit']:
                    print("Encerrando conversa... Voltando ao menu.")
                    break
                elif "hora" in pergunta.lower():
                    print(f"Jarvis: A hora atual é {functions.obter_hora()}.")
                    continue
                elif "data" in pergunta.lower():
                    print(f"Jarvis: A data atual é {functions.obter_data()}.")
                    continue
                print("Jarvis pensando...", end="\r")
                resposta = ollama_brain.perguntar(pergunta)
                print(f"Jarvis: {resposta}")
        elif opcao == 0:
            return False
        else:
            print("Opção inválida!")

    except ValueError:
        print("Por favor, digite um número.")

    return True

if __name__ == "__main__":
    user_nome, user_idade = iniciar_sistema()

    while True:
        menu()
        if not script(user_nome, user_idade):
            print("Encerrando o sistema... Até logo!")
            break

        # Opcional: Perguntar se quer continuar ou apenas voltar ao menu
        # Aqui vou fazer voltar ao menu automaticamente para ser mais fluido
