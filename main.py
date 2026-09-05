import time
import functions
from brain import ollama_brain

def iniciar_sistema():
    print("--- Inicializando Omega ---")
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

    print(f"\nOlá, {nome}! Bem-vindo(a) ao sistema. Eu sou o Omega.")
    return nome, idade

def menu():
    print('\n' + '='*30)
    print(' O que deseja fazer?')
    print('='*30)
    print('1 - Conversar com Omega')
    print('0 - Sair')
    print('='*30)

def script(nome, idade, memoria):
    try:
        opcao = int(input("Digite a opção desejada: "))

        if opcao == 1:
            print("\n--- Modo de Conversa Ativado (Digite 'sair' para voltar ao menu) ---")
            while True:
                pergunta = input(f"{nome}: ")
                if pergunta.lower() in ['sair', 'exit', 'quit']:
                    print("Encerrando conversa... Voltando ao menu.")
                    break

                # Tratamento de hora/data com salvamento na memória
                if "hora" in pergunta.lower():
                    res_hora = f"A hora atual é {functions.obter_hora()}."
                    print(f"Omega: {res_hora}")
                    memoria.append({'role': 'user', 'content': pergunta})
                    memoria.append({'role': 'assistant', 'content': res_hora})
                    functions.salvar_memoria(memoria)
                    continue
                elif "data" in pergunta.lower():
                    res_data = f"A data atual é {functions.obter_data()}."
                    print(f"Omega: {res_data}")
                    memoria.append({'role': 'user', 'content': pergunta})
                    memoria.append({'role': 'assistant', 'content': res_data})
                    functions.salvar_memoria(memoria)
                    continue

                # Fluxo normal de IA:
                memoria.append({'role': 'user', 'content': pergunta})
                functions.salvar_memoria(memoria)

                print("Omega pensando...", end="\r")
                resposta = ollama_brain.perguntar(pergunta, memoria)
                print(f"Omega: {resposta}")

                memoria.append({'role': 'assistant', 'content': resposta})
                functions.salvar_memoria(memoria)

        elif opcao == 0:
            return False
        else:
            print("Opção inválida!")

    except ValueError:
        print("Por favor, digite um número.")

    return True

if __name__ == "__main__":
    user_nome, user_idade = iniciar_sistema()

    # Carregamos a memória do arquivo JSON logo ao iniciar
    memoria_global = functions.carregar_memoria()

    # Se a memória estiver vazia, definimos a personalidade do Omega
    if not memoria_global:
        memoria_global.append({
            'role': 'system',
            'content': 'Você é Omega, um assistente pessoal inteligente. Sua principal missão é aprender e se adaptar à personalidade, tom e preferências do usuário ao longo do tempo, tornando-se um reflexo perfeito de suas necessidades.'
        })
        functions.salvar_memoria(memoria_global)

    while True:
        menu()
        if not script(user_nome, user_idade, memoria_global):
            print("Encerrando o sistema... Até logo!")
            break
