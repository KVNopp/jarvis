import time


nome = input("Digite seu nome: ")
idade = int(input("Digite sua idade: "))
if idade <18:
    print("Você é menor de idade.")
else:
    print("Você é maior de idade.")
senha = 777
tentativa = int(input("Digite a senha para continuar: "))
if tentativa == senha:
    print("Senha correta! Acesso concedido.")
else:
    print("Senha incorreta! Acesso negado.")
    while tentativa != senha:
        tentativa = int(input("Digite a senha novamente: "))
        if tentativa == senha:
            print("Senha correta! Acesso concedido.")
        else:
            print("Senha incorreta! Tente novamente.")
            time.sleep(3+1)  # Pausa de 1 segundo antes de permitir nova tentativa
print(f"Olá, {nome}! Bem-vindo(a) ao programa.")
print('como eu posso ajuadar você?')
time.sleep(2)
print('1 - Para saber a hora atual')
print('2 - Para saber a data atual')
print('3 - Para saber a sua idade em dias')
hora = time.localtime()
data = time.localtime()
idade_dias = idade * 365
opcao = int(input("Digite a opção desejada: "))
if opcao == 1:
    print(f"Hora atual: {hora.tm_hour}:{hora.tm_min}:{hora.tm_sec}")
elif opcao == 2:
    print(f"Data atual: {data.tm_mday}/{data.tm_mon}/{data.tm_year}")
elif opcao == 3:
    print(f"Sua idade em dias é: {idade_dias} dias")

while True:
        resposta = input("Deseja continuar? (s/n): ")
        if resposta.lower() == 's':
            print('como eu posso ajuadar você?')
            time.sleep(2)
            print('1 - Para saber a hora atual')
            print('2 - Para saber a data atual')
            print('3 - Para saber a sua idade em dias')
            opcao = int(input("Digite a opção desejada: "))
            if opcao == 1:
                print(f"Hora atual: {hora.tm_hour}:{hora.tm_min}:{hora.tm_sec}")
            elif opcao == 2:
                print(f"Data atual: {data.tm_mday}/{data.tm_mon}/{data.tm_year}")
            elif opcao == 3:
                print(f"Sua idade em dias é: {idade_dias} dias")
        elif resposta.lower() == 'n':
            print("Encerrando o programa. Até logo!")
            break
        else:
            print("Opção inválida. Digite 's' para sim ou 'n' para não.")
