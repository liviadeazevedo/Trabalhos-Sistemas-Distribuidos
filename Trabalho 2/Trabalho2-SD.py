import socket
import threading
import time
from random import randint
import fcntl
import struct

import sys #Para obter os argumentos passados ao programa --> python [nome].py [interface da subrede]

mensagens = []

pidLider = -1
MAX_RELOGIO = 10
DELAY_RELOGIO = 1
INTERVALO_PAUSA_THREAD_ESCUTADORA = 3
TIMEOUT_INTERVAL = 6
TIMEOUT_INTERVAL_INSTATANEO = 1

INTERFACE_SUBREDE = sys.argv[1]
PORTA = 8881
MAX_TAM_MENSAGEM = 8192
DECODING = 'utf-8'

#Encontrado em: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/1947766
def getIpAddress(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], DECODING))
    )[20:24])

def getBroadcastAddress(ifname):
    end = getIpAddress(ifname)
    partsIp = end.split('.') #Separar as partes do IP
    partsIp.pop() #Eliminar o ultimo elemento identificador
    broadEnd = ''

    for elem in partsIp:
        broadEnd = broadEnd + elem + '.'
    broadEnd = broadEnd + '255'

    return broadEnd
    
END_LOCAL_BROADCAST = getBroadcastAddress(INTERFACE_SUBREDE)

class Conexao():
    def __init__(self,endBroadcast,porta,interfaceSubRede):
        self.endBroadcast = endBroadcast
        self.porta = porta
        self.idConexao = int(getIpAddress(interfaceSubRede).split('.')[-1])
        self.socketComm = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ipSubRede = getIpAddress(interfaceSubRede)
        
        self.timeoutIntervalPadrao = self.socketComm.gettimeout()
        
    def habilitarTimeOut(self):
        self.socketComm.settimeout(TIMEOUT_INTERVAL)
    
    def desabilitarTimeOut(self):
        self.socketComm.settimeout(self.timeoutIntervalPadrao)
        
    def habilitarTimeOutInstantaneo(self):
        self.socketComm.settimeout(TIMEOUT_INTERVAL_INSTATANEO)
        
    def getId(self):
        return self.idConexao
    
    def getIP(self):
        return self.ipSubRede
    
    def iniciarConexao(self):
        self.socketComm.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) 
        self.socketComm.bind(('',self.porta))
    
    def enviarMensagem(self,msg,end=END_LOCAL_BROADCAST): #Msg deve ser String.
        MensagensLog.envioMensagem(end, msg)
        self.socketComm.sendto(bytes(msg,DECODING),(end,self.porta))
    
    def obterIpPeloId(self, id):
        return self.endBroadcast[:-3] + str(id)
    
    def enviarMensagemPeloId(self, msg, id=255):
        self.enviarMensagem(msg, self.obterIpPeloId(id))

    def receberMensagem(self):
        msg,addr = self.receberMensagemComEnd()
        return msg
    
    def receberMensagemComEnd(self):
        msg, addr = self.socketComm.recvfrom(MAX_TAM_MENSAGEM)
        msg = msg.decode(DECODING)
        MensagensLog.recebimentoMensagem(addr, msg, self)
        return (msg, addr[0])
    
class MensagensHelper():
    TIPOMSG_OK = 1
    TIPOMSG_ELEICAO = 2
    TIPOMSG_NOVOLIDER = 3
    
    TIPOMSG_RELOGIO = 4
    TIPOMSG_DIFERENCA_RELOGIO = 5
    TIPOMSG_ATUALIZACAO_RELOGIO = 6
    
    separador = ';'
    constEleicao = "ELEICAO"
    constNovoLider = "LIDER"
    constOk = "ok"
    
    constRelogio = "ENVIO_RELOGIO"
    constDiferencaRelogio = "DIFERENCA_RELOGIO"
    constAtualizacaoRelogio = "ATUALIZACAO_RELOGIO"
    
    @staticmethod
    def criarMensagemEleicao(id):
        return MensagensHelper.constEleicao + MensagensHelper.separador + str(id)
    
    @staticmethod
    def criarMensagemNovoLider(id):
        return MensagensHelper.constNovoLider + MensagensHelper.separador + str(id)
        
    @staticmethod
    def criarMensagemEnvioRelogioBerckley(relogio):
        return MensagensHelper.constRelogio + MensagensHelper.separador + str(relogio)
        
    @staticmethod
    def criarMensagemDiferencaRelogioBerckley(id,diferenca):
        return MensagensHelper.constDiferencaRelogio + MensagensHelper.separador + str(id) + MensagensHelper.separador + str(diferenca)
    
    @staticmethod
    def criarMensagemAtualizacaoRelogioBerckley(valorAtualizar):
        return MensagensHelper.constAtualizacaoRelogio + MensagensHelper.separador + str(valorAtualizar)

    @staticmethod
    def retirarIdDaMensagem(msg):
        return int(msg.split(MensagensHelper.separador)[1])
        
    @staticmethod
    def retirarRelogioDaMensagem(msg):
        return int(msg.split(MensagensHelper.separador)[1])

    @staticmethod
    def retirarDiferencaDaMensagem(msg):
        return int(msg.split(MensagensHelper.separador)[2])
        
    @staticmethod
    def retirarValorAtualizarDaMensagem(msg):
        return int(msg.split(MensagensHelper.separador)[1])
    
    @staticmethod
    def defineTipoMensagem(msg):
        if(msg == MensagensHelper.constOk):
            return MensagensHelper.TIPOMSG_OK
        elif(msg.split(MensagensHelper.separador)[0] == MensagensHelper.constEleicao):
            return MensagensHelper.TIPOMSG_ELEICAO
        elif(msg.split(MensagensHelper.separador)[0] == MensagensHelper.constNovoLider):
            return MensagensHelper.TIPOMSG_NOVOLIDER
        elif(msg.split(MensagensHelper.separador)[0] == MensagensHelper.constRelogio):
            return MensagensHelper.TIPOMSG_RELOGIO
        elif(msg.split(MensagensHelper.separador)[0] == MensagensHelper.constDiferencaRelogio):
            return MensagensHelper.TIPOMSG_DIFERENCA_RELOGIO
        elif(msg.split(MensagensHelper.separador)[0] == MensagensHelper.constAtualizacaoRelogio):
            return MensagensHelper.TIPOMSG_ATUALIZACAO_RELOGIO
        else:
            return -1
        
#classe da thread que incrementa o relogio
class ClockThread(threading.Thread):
    def __init__(self, passo, delay):
        threading.Thread.__init__(self)
        self.passo = passo
        self.relogio = 0
        self.delay = delay
        self.terminou = False
        
    def run(self):
        while( not self.terminou):
            time.sleep(self.delay)
            self.relogio += self.passo
    
    def setRelogio(self, novoRelogio):
        self.relogio = novoRelogio
    
    def getRelogio(self):
        return self.relogio

    def terminar(self):
        self.terminou = True

#classe da thread que escuta a comunicação de outros processos(inicio eleição)
class ListenCommThread(threading.Thread):
    def __init__(self, commObj):
        threading.Thread.__init__(self)
        self.commObj = commObj
        self.terminou = False
        self.pausa = False
        
    def run(self):
        while(not self.terminou):
            if(not self.pausa):
                try:
                    self.commObj.habilitarTimeOutInstantaneo()
                    msg = self.commObj.receberMensagem()
                    self.entregaMensagem(msg)
                    self.commObj.desabilitarTimeOut()
                except socket.timeout:
                    pass
                finally:
                    self.commObj.desabilitarTimeOut()
            else:
                time.sleep(INTERVALO_PAUSA_THREAD_ESCUTADORA)
    
    def entregaMensagem(self, mensagem):
        mensagens.append(mensagem)
    
    def terminar(self):
        self.terminou = True
    
    def togglePausa(self):
        self.pausa = not self.pausa
        self.commObj.desabilitarTimeOut()
        
#classe da thread que escuta o teclado
class ListenInputThread(threading.Thread):
    def __init__(self,myid):
        threading.Thread.__init__(self)
        self.myId = myid
        self.terminou = False
        self.pausa = False
    def run(self):
        while(not self.terminou):
            if(not self.pausa):
                input()
                mensagens.append(MensagensHelper.criarMensagemEleicao(self.myId))
            else:
                time.sleep(INTERVALO_PAUSA_THREAD_ESCUTADORA)
                    
    def terminar(self):
        self.terminou = True
    
    def togglePausa(self):
        self.pausa = not self.pausa

class MensagensLog():

    @staticmethod
    def inicioConexao():
        print(">>> Inicio Conexão...\n")
    
    @staticmethod
    def fimConexao():
        print(">>> Fim Conexão...Aperter ENTER para sair.\n")

    @staticmethod
    def inicioThreads():
        print("---------------------------------------------------------------------------\n")
        print("Inicio contagem do Relógio...")
        print("Espera para inicío da Eleição...")
        print("Aperte ENTER ou aguarde a chegada de uma mensagem...\n")
        print("---------------------------------------------------------------------------\n")

    @staticmethod
    def inicioAlgoritmo(alg):
        print("------------------------------- INICIO %s! -----------------------------\n" % alg)

    @staticmethod
    def fimAlgoritmo(alg):
        print("----------------------------- FIM %s! ------------------------------\n" % alg)

    @staticmethod
    def limpaMensagensRecebidas():
        print(">>> Lixo de mensagens armazenado esvaziado.\n")

    @staticmethod
    def pausaThreads():
        print(">>> PAUSE ATIVO nas threads Receptora e Teclado...\n")

    @staticmethod
    def resumeThreads():
        print(">>> PAUSE SUSPENSO nas threads Receptora e Teclado...\n")

    @staticmethod
    def envioMensagem(destinatario,msg):
        if destinatario != END_LOCAL_BROADCAST:
            print(">>> ENVIO para %s : %s \n" % (destinatario,str(msg)))
        else:
            print(">>> ENVIO em BROADCAST : %s \n" % str(msg))

    @staticmethod
    def recebimentoMensagem(remetente,msg,commObj):
        if commObj.getIP() != remetente[0]:
            print(">>> RECEBIDO de %s : %s \n" % (remetente,str(msg)))

    @staticmethod
    def relogioAtualizadoPara(valor):
        print(">>> RELOGIO ATUALIZADO: %s\n " % valor)
    
    @staticmethod
    def relogioAtualComo(valor):
        print(">>> RELOGIO ATUAL: %s\n" % valor)
    
    @staticmethod
    def definicaoLider(lider,meuId):
        print(">>> LIDER: %s\n    Meu ID: %s\n" % (lider,meuId))

    @staticmethod
    def listaDeDiferencasRelogiosRecebida(listaRelogio):
        print(">>> Lista de Diferenças recebidas: %s\n" % str(listaRelogio))
        
    @staticmethod
    def atualizacaoDosRelogios(relogio,diff):
        print(">>> DIFERENÇA MÉDIA CALCULADA: %s\n    ATUALIZAÇÃO RELÓGIOS em BROADCAST: %s\n" % (str(diff),str(relogio)))

    @staticmethod
    def relogioLiderRecebido(relogio):
        print(">>> RELOGIO LIDER: %s\n" % str(relogio))

    @staticmethod
    def diferencaDeRelogioEnviada(diff):
        print(">>> DIFERENÇA RELOGIO com o Líder: %s\n" % str(diff))

    @staticmethod
    def relogioAtualizadoPeloLider(relogio):
        print(">>> RELOGIO ATUALIZADO pelo Líder: %s\n" % str(relogio))
    
    @staticmethod
    def erroInesperadoBully():
        print("XXX--> Erro inesperado no Bully...Começando com uma mensagem de OK <--XXX\n")
    
    @staticmethod
    def ignorarMensagem(msg):
        print("---> Mensagem ignorada: %s <---\n" % msg)
    
    @staticmethod
    def erroInesperadoBerkeleyEnvioRelogio():
        print("XXX--> Erro inesperado no Berkeley...Esperando um envio de relógio e recebendo algo diferente <--XXX\n")
    
    @staticmethod
    def erroInesperadoBerkeleyAtualizacaoRelogio():
        print("XXX--> Erro inesperado no Berkeley...Recebeu uma mensagem diferente de atualização do relogio <--XXX\n")

#Command bully
class BullyCommand():
    def __init__(self, commObj, myid):
        self.commObj = commObj
        self.myId = myid

    def exec(self):
        global pidLider

        while len(mensagens) != 0:
            msgRecebida = mensagens.pop()

            if(MensagensHelper.defineTipoMensagem(msgRecebida) == MensagensHelper.TIPOMSG_NOVOLIDER):
                pidLider = MensagensHelper.retirarIdDaMensagem(msgRecebida)
                return 1

            if(MensagensHelper.defineTipoMensagem(msgRecebida) != MensagensHelper.TIPOMSG_ELEICAO):
                MensagensLog.erroInesperadoBully()
                return -1

            idIniciador = MensagensHelper.retirarIdDaMensagem(msgRecebida)

            if(idIniciador < self.myId):
                self.commObj.enviarMensagemPeloId(MensagensHelper.constOk, idIniciador)
        
        mensagem = MensagensHelper.criarMensagemEleicao(self.myId)
        
        self.commObj.enviarMensagem(mensagem) #Envio broadcast, parametro padrão
        
        ehLider = True

        try:
            while True:
                self.commObj.habilitarTimeOut()
                msg, end = self.commObj.receberMensagemComEnd()
                tipoMsg = MensagensHelper.defineTipoMensagem(msg)

                if(tipoMsg == MensagensHelper.TIPOMSG_OK):
                    ehLider = False
                    continue
                    
                if(tipoMsg == MensagensHelper.TIPOMSG_NOVOLIDER):
                    pidLider = MensagensHelper.retirarIdDaMensagem(msg) 

                if(tipoMsg == MensagensHelper.TIPOMSG_ELEICAO):
                    idIniciador = MensagensHelper.retirarIdDaMensagem(msg)

                    if(idIniciador < self.myId):
                        self.commObj.enviarMensagem(MensagensHelper.constOk, end)         

        except socket.timeout:
            pass
        finally:
            self.commObj.desabilitarTimeOut()
        
        if(pidLider != -1):
            return 1
        
        if(not ehLider):
            while True:
                msg, end = self.commObj.receberMensagemComEnd()
                
                if(MensagensHelper.defineTipoMensagem(msg) == MensagensHelper.TIPOMSG_ELEICAO):
                    idIniciador = MensagensHelper.retirarIdDaMensagem(msg)

                    if(idIniciador < self.myId):
                        self.commObj.enviarMensagem(MensagensHelper.constOk, end)
                
                if(MensagensHelper.defineTipoMensagem(msg) != MensagensHelper.TIPOMSG_NOVOLIDER):
                    continue
                pidLider = MensagensHelper.retirarIdDaMensagem(msg) 
                break             
        else:
            pidLider = self.myId
            time.sleep(TIMEOUT_INTERVAL)
            self.commObj.enviarMensagem(MensagensHelper.criarMensagemNovoLider(self.myId)) #Mensagem em broadcast, parametro padrão

        return 1

#Command Berkeley
class BerkeleyCommand():
    def __init__(self, commObj, myid, threadRelogio):
        self.commObj = commObj
        self.myId = myid
        self.listaDifRelogios = []
        self.threadRelogio = threadRelogio
    
    def calculaMediaRelogios(self):
        return round(sum({relogio for id, relogio in self.listaDifRelogios}) / len(self.listaDifRelogios))
    
    def exec(self):
        relogioAtual = self.threadRelogio.getRelogio() #Lembre-se que essa variável está sempre se modificando...
        MensagensLog.relogioAtualComo(str(relogioAtual))

        if self.myId == pidLider:
            self.listaDifRelogios.append((self.myId,0))
            time.sleep(TIMEOUT_INTERVAL)
            self.commObj.enviarMensagem(MensagensHelper.criarMensagemEnvioRelogioBerckley(relogioAtual)) #Envio broadcast do relogio atual.
            
            #Receber os relogios dos outros processos
            self.commObj.habilitarTimeOut() #6 segundos para esperar resposta de cada processo
            try:
                while True:
                    msg = self.commObj.receberMensagem()
                    tipoMsg = MensagensHelper.defineTipoMensagem(msg)
                    
                    if(tipoMsg == MensagensHelper.TIPOMSG_DIFERENCA_RELOGIO):
                        pid = MensagensHelper.retirarIdDaMensagem(msg)
                        diferencaRecebida = MensagensHelper.retirarDiferencaDaMensagem(msg)
                        self.listaDifRelogios.append((pid,diferencaRecebida))
                    else:
                        MensagensLog.ignorarMensagem(msg)
                        
            except socket.timeout:
                pass
            finally:
                self.commObj.desabilitarTimeOut()
                
            MensagensLog.listaDeDiferencasRelogiosRecebida(self.listaDifRelogios)

            #Calcular a média a ser atualizada no relogioAtual
            media = self.calculaMediaRelogios()
            relogioAtual = relogioAtual + media

            MensagensLog.atualizacaoDosRelogios(relogioAtual,media)
            
            for pid, diff in self.listaDifRelogios:
                self.commObj.enviarMensagemPeloId(MensagensHelper.criarMensagemAtualizacaoRelogioBerckley(media - diff), pid)

        else:
            msg = self.commObj.receberMensagem()
            tipoMsg = MensagensHelper.defineTipoMensagem(msg)
            
            if(tipoMsg != MensagensHelper.TIPOMSG_RELOGIO):
                MensagensLog.erroInesperadoBerkeleyEnvioRelogio()
                return -1
        
            relogioLider = MensagensHelper.retirarRelogioDaMensagem(msg)
            MensagensLog.relogioLiderRecebido(relogioLider)
            
            diff = relogioAtual - relogioLider
            MensagensLog.diferencaDeRelogioEnviada(diff)
            
            self.commObj.enviarMensagemPeloId(MensagensHelper.criarMensagemDiferencaRelogioBerckley(self.myId,diff), pidLider)
            
            msg = self.commObj.receberMensagem()
            
            if(MensagensHelper.defineTipoMensagem(msg) != MensagensHelper.TIPOMSG_ATUALIZACAO_RELOGIO):
                MensagensLog.erroInesperadoBerkeleyAtualizacaoRelogio()
                return -1
            
            valorAtualizar = MensagensHelper.retirarValorAtualizarDaMensagem(msg)
            
            relogioAtual = relogioAtual + valorAtualizar
            MensagensLog.relogioAtualizadoPeloLider(relogioAtual)

        self.listaDifRelogios.clear()
        self.threadRelogio.setRelogio(relogioAtual)
        
def main():
    MensagensLog.inicioConexao()
    commObj = Conexao(END_LOCAL_BROADCAST,PORTA,INTERFACE_SUBREDE)
    commObj.iniciarConexao()

    passo = randint(1,MAX_RELOGIO)
    trelogio = ClockThread(passo, DELAY_RELOGIO)
    threadReceptoraExterna = ListenCommThread(commObj)
    threadReceptoraTeclado = ListenInputThread(commObj.getId())

    cmdBully = BullyCommand(commObj, commObj.getId())
    cmdBerkeley = BerkeleyCommand(commObj, commObj.getId(), trelogio)
    
    MensagensLog.inicioThreads()
    trelogio.start()
    threadReceptoraExterna.start()
    threadReceptoraTeclado.start()

    end = False

    while( not end):
        if(len(mensagens) == 0):
            continue

        MensagensLog.pausaThreads()
        threadReceptoraExterna.togglePausa()
        threadReceptoraTeclado.togglePausa()

#        ------Algoritmo do Bully
        MensagensLog.inicioAlgoritmo('BULLY')
        cmdBully.exec()
        MensagensLog.fimAlgoritmo('BULLY')

        MensagensLog.definicaoLider(str(pidLider),str(commObj.getId()))

        threadReceptoraExterna.togglePausa()
        threadReceptoraTeclado.togglePausa()
        MensagensLog.resumeThreads()

        time.sleep(INTERVALO_PAUSA_THREAD_ESCUTADORA)
        
        MensagensLog.limpaMensagensRecebidas()
        mensagens.clear()

        MensagensLog.pausaThreads()
        threadReceptoraExterna.togglePausa()
        threadReceptoraTeclado.togglePausa()

#        ------Algoritmo de Berkeley
        MensagensLog.inicioAlgoritmo('BERKELEY')
        relogioAtual = cmdBerkeley.exec()
        MensagensLog.fimAlgoritmo('BERKELEY')

        MensagensLog.relogioAtualizadoPara(trelogio.getRelogio())
        MensagensLog.resumeThreads()
        
        MensagensLog.limpaMensagensRecebidas()
        mensagens.clear()

        end = True

    MensagensLog.fimConexao()
    trelogio.terminar()
    threadReceptoraExterna.terminar()
    threadReceptoraTeclado.terminar()

if __name__ == '__main__':
    main()