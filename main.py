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