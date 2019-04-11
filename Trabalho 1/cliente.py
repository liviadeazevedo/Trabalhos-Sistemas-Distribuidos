import xmlrpc.client

PORTA = "8000"
ENDERECO = "localhost"
ENDERECO_SERVIDOR = "http://" + ENDERECO + ":" + PORTA + "/"

end = -1
op = -1
mat = -1
cod_disc = -1
nota = -1

with xmlrpc.client.ServerProxy(ENDERECO_SERVIDOR) as proxy:
	while end != 0:
		print(proxy.iniciar())
		
		while op not in [1,2,3,4]:
			try:
				op = int(input("Selecione a opção correspondente a ação desejada:\n"))
				if op not in [1,2,3,4]:
					print("OPÇÃO INVÁLIDA.")
			except ValueError:
				print("OPÇÃO INVÁLIDA.")
				op = -1				
					
		mat = input("Digite a matrícula do aluno:\n").upper()
		
		if op == 1:
			cod_disc = input("Digite o código da disciplina:\n").upper()
			
			while nota == -1:
				try:
					nota = input("Digite a nota a ser cadastrada(Ex: 8.1, 9.15):\n")
					float(nota)
				except ValueError:
					print("NOTA INVÁLIDA.")
					nota = -1

		elif op == 2:
			cod_disc = input("Digite o código da disciplina:\n").upper()
				
		print(proxy.executar(op,mat,cod_disc,nota))
		
		while end not in [0,1]:
			try:
				end = int(input("Deseja realizar mais alguma operação? (\"1\" para continuar ou \"0\" para sair)\n"))
				if end not in [0,1]:
					print("OPÇÃO INVÁLIDA.")
			except ValueError:
				print("OPÇÃO INVÁLIDA.")
									
		if end == 0:
			print(proxy.finalizar())
		else:
			op = -1
			end = -1
			mat = -1
			cod_disc = -1
			nota = -1
