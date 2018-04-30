import socket
import time
import threading
import pyevent
import os


class TcpClient:
    """docstring for TcpClient"""

    Event_Client_Recv = 'Recv'

    def __init__(self, ip, port,timeout=2,needPrint=False,needfixMixPackets=False):
        self.__eventManager = pyevent.EventManager()
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.isconnected = False
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.settimeout(self.timeout)         
        self.__flag_wait = False
        self.__needPrint = needPrint
        self.__needfixMixPackets = needfixMixPackets
        self.__badmsg = ''
        self.__eventManager.start()
        self.EVENT_CONNECT_SUCCESS = pyevent.Event(self.__eventManager,'EVENT_CONNECT_SUCCESS')
        self.EVENT_CONNECT_FAIL = pyevent.Event(self.__eventManager,'EVENT_CONNECT_FAIL')
        self.EVENT_SEND_MESSAGE = pyevent.Event(self.__eventManager,'EVENT_SEND_MESSAGE')
        self.EVENT_RECEIVE_MESSAGE = pyevent.Event(self.__eventManager,'EVENT_RECEIVE_MESSAGE')


    def connect(self):
        try:
            if not self.isconnected:
                self.__socket.connect((self.ip, self.port))
                if self.__needPrint:
                    print 'Connect success'
                self.EVENT_CONNECT_SUCCESS.emit()
                self.isconnected = True
                t = threading.Thread(target=self.__listenRecv)
                t.setDaemon(True)
                t.start()
            else:
                if self.__needPrint:
                    print 'Already connected'
            
        except Exception, e:
            self.EVENT_CONNECT_FAIL.emit()
            if self.__needPrint:
                print 'Connect fail, %s'%e

    def disconnect(self):
        self.__socket.close()
        self.isconnected = False

    def send(self, msg):
        try:
            if self.__needfixMixPackets:
                msgfix = msg + '</a/b>'
            else:
                msgfix = msg
            self.__socket.send(msgfix.encode('utf-8'))
            self.EVENT_SEND_MESSAGE.emit(msg)
            if self.__needPrint:
                print 'Client send :', msg.replace('\r','\\r').replace('\n','\\n')[:-2]
            return 0
        except Exception:
            return 1


    def __listenRecv(self):
        while self.isconnected:
            recvdata = ''
            try:
                recvdata = self.__socket.recv(1024)
                if recvdata != '':
                    if self.__needfixMixPackets: 
                        if recvdata[-6:] == '</a/b>':
                            recvmsg = recvdata.split('</a/b>')
                            if self.__badmsg != '':
                                piece = self.__badmsg + recvmsg[0]
                                newmsg = piece.split('</a/b>')
                                recvmsg.pop(0)
                                for msg in newmsg[::-1]:
                                    if msg != '':
                                        recvmsg.insert(0,msg)
                                self.__badmsg = ''
                            for msg in recvmsg:
                                if msg != '':
                                    self.EVENT_RECEIVE_MESSAGE.emit((self,msg))
                                    if self.__needPrint:
                                        print 'Client receive : "%s"'%msg.replace('\r','\\r').replace('\n','\\n')[:-2]
                        else:
                            recvmsg = recvdata.split('</a/b>')
                            if self.__badmsg != '':
                                piece = self.__badmsg + recvmsg[0]
                                newmsg = piece.split('</a/b>')
                                recvmsg.pop(0)
                                for msg in newmsg[::-1]:
                                    if msg != '':
                                        recvmsg.insert(0,msg)
                                self.__badmsg = ''
                            for msg in recvmsg[:-1]:
                                if msg != '':
                                    self.EVENT_RECEIVE_MESSAGE.emit((self,msg))
                                    if self.__needPrint:
                                        print 'Client receive : "%s"'%msg.replace('\r','\\r').replace('\n','\\n')[:-2]
                            self.__badmsg = recvmsg[-1]
                    else:
                        self.EVENT_RECEIVE_MESSAGE.emit((self,recvdata))
                        if self.__needPrint:
                            print 'Client receive : "%s"'%recvdata.replace('\r','\\r').replace('\n','\\n')[:-2]
                else:
                    time.sleep(0.001)
            except Exception as e:
                # if self.__needPrint:
                #     print e.args
                pass
            
    def __pingServer(self):
        result = os.system('ping -c 1 -t 1 '+self.ip)
        if result:
            self.isconnected = False
            return False
        else:
            return True

    def checkConnection(self):
        if self.isconnected:
            return self.__pingServer()
        else:
            return False

if __name__ == '__main__':
    client = TcpClient('127.0.0.1',4097,needPrint=True)
    client.connect()
    # client.send('11111,INPUT_ERROR,123')
    # client.send('11111,AUTOMATION_ACT_COMPLETED,100\r')
    # client.send('12121,ADD_UUT,100,1')
    time.sleep(5)
    # client.send('11111,OUTPUT_ERROR,123')
    client.send('12121,ADD_UUT,101,1\r')
    # client.send('22222,AUTOMATION_ACT_COMPLETED,101\r')
    # time.sleep(5)
    # client.send('33333,AUTOMATION_ACT_COMPLETED,100\r')
    # time.sleep(15)
    # client.send('44444,AUTOMATION_ACT_COMPLETED,101\r')
    time.sleep(5)
    client.disconnect()
