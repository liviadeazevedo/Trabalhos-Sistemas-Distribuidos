import xmlrpc.server
import threading as t
import os

NOME_ARQUIVO_NOTAS = "notas.txt"
ENDERECO = "localhost"
PORTA = 8000
DELIMITADOR = "\t"
STRING_SEP = "\n----------------------------------------------------------------------------\n"

#Funções do API do Servidor.

###		Métodos que devem ser implementados		###
def cadastrar_nota(mat,cod_disc,nota):
	"""Deve armazenar a nota obtida pelo aluno com matrícula mat na disciplina cod_disc.Se a nota já existir, deve ser sobreescrita."""
		
	with open(NOME_ARQUIVO_NOTAS,"r+") as f:
		novo_dado = mat + DELIMITADOR + cod_disc + DELIMITADOR
		dados = f.readlines()
	
		for i in range(len(dados)):
			if novo_dado in dados[i]: #Nota já existe
				dados[i] = novo_dado + str(round(float(nota),2)) + "\n"
				f.close()
				with open(NOME_ARQUIVO_NOTAS,"w") as f:
					f.writelines(dados)
				return STRING_SEP + "Nota existente sobreescrita com sucesso!" + STRING_SEP

		#Nota não existe
		f.write(novo_dado + str(round(float(nota),2)) + "\n")
		return STRING_SEP + "Nova nota cadastrada com sucesso!" + STRING_SEP

		
def consultar_nota(mat,cod_disc):
	"""Retorna a nota do aluno de matrícula mat na disciplina cod_disc. Se não existir nota cadastrada, uma mensagem de erro deve ser retornada."""
		
	with open(NOME_ARQUIVO_NOTAS,"r") as f:
		aluno = mat + DELIMITADOR + cod_disc + DELIMITADOR
		dados = f.readlines()
		
		for i in range(len(dados)):
			if aluno in dados[i]:
				return STRING_SEP + "Matrícula " + mat + " na Disciplina " + cod_disc + ": " + dados[i].split(DELIMITADOR)[-1][0:-1] + STRING_SEP
		
		return STRING_SEP + "Nota de aluno não cadastrada no sistema." + STRING_SEP
	

def consultar_notas(mat):
	"""Retorna uma lista com todas as notas cadastradas para o aluno com matrícula mat. Se não existir nota cadastrada, uma mensagem de erro deve ser retornada."""
	
	with open(NOME_ARQUIVO_NOTAS,"r") as f:
		aluno = mat + DELIMITADOR
		dados = f.readlines()
		notas_aluno = []
		
		for i in range(len(dados)):
			if aluno in dados[i]:
				notas_aluno.append((dados[i].split(DELIMITADOR)[-1][0:-1],dados[i].split(DELIMITADOR)[-2])) #tuplas (nota,cod_disc)
		
		if notas_aluno: #lista tem notas
			return STRING_SEP + "Lista (nota,codigo disciplina): " + str(notas_aluno) + STRING_SEP
		else:
			return STRING_SEP + "Nenhuma nota cadastrada para este aluno no sistema." + STRING_SEP
	
	
def consultar_cr(mat):
	"""Deve retornar o CR do aluno com matrícula mat. O cálculo do CR é uma média simples de todas as notas cadastradas para aquele aluno. Se não existir nota cadastrada, uma mensagem de erro deve ser retornada."""
		
	with open(NOME_ARQUIVO_NOTAS,"r") as f:
		aluno = mat + DELIMITADOR
		dados = f.readlines()
		sum_notas = 0.0
		count = 0
	
		for i in range(len(dados)):
			if aluno in dados[i]:
				sum_notas += round(float(dados[i].split(DELIMITADOR)[-1][0:-1]),2)
				count += 1
	
		if sum_notas != 0.0:
			cr = round(sum_notas/count,2)
			return STRING_SEP + "CR médio do aluno de Matrícula " + mat + ": " + str(cr) + STRING_SEP
		else:
			return STRING_SEP + "Nenhuma nota cadastrada para este aluno no sistema." + STRING_SEP


###		Métodos de interface com o cliente		###

def iniciar():
	string_apres = "\n########## Repositório de Notas ##########\n\n"
	string_apres += "Lista de métodos disponíveis na API do Servidor do Repositório de Notas:\n\n"
	string_apres += "\t1 - Cadastrar Notas\n\t2 - Consultar Nota\n\t3 - Consultar Notas\n\t4 - Consultar CR\n"
	string_apres += "################################################################################\n\n"
	
	if not os.path.isfile(os.getcwd() + "/" + NOME_ARQUIVO_NOTAS):
		f = open(NOME_ARQUIVO_NOTAS,"w+")
		f.close()
	
	return string_apres	

def executar(num_metodo,mat,cod_disc=-1,nota=-1): #Todos os retornos dos métodos devem ser string!
	if num_metodo == 1:
		return cadastrar_nota(mat,cod_disc,nota)
	elif num_metodo == 2:
		return consultar_nota(mat,cod_disc)
	elif num_metodo == 3:
		return consultar_notas(mat)
	elif num_metodo == 4:
		return consultar_cr(mat)

	
###		Métodos auxiliares de execução		###

class ShutdownThread(t.Thread):
   
   def __init__(self, threadID):
   	t.Thread.__init__(self)
   	self.threadID = threadID
   	
   def run(self):
   	servidor.shutdown()

def finalizar():
	thread = ShutdownThread(1)
	thread.start()
	print("Iniciou o término de conexão do servidor...")
	print("Conexão do Servidor finalizada")
	return "Conexão com o Servidor finalizada"

#Inicialização do Servidor.

servidor = xmlrpc.server.SimpleXMLRPCServer((ENDERECO, PORTA))
print("Ouvindo na porta " + str(PORTA) + "...")
servidor.register_function(iniciar)
servidor.register_function(finalizar)
servidor.register_function(executar)
servidor.serve_forever()

