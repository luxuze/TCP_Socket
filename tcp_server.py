import socket
import time
import threading
import pyevent
import select


class TcpServer(object):
    """docstring for SocketServer"""

    def __init__(self, ip, port, maxLink=5, needPrint=False, needfixMixPackets=False):

        self.__eventManager = pyevent.EventManager()
        self.ip = ip
        self.port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind((ip, port))
        self.__socket.settimeout(2)
        self.__socket.listen(maxLink)
        self.__needPrint = needPrint
        self.isListening = False
        self.__needfixMixPackets = needfixMixPackets
        self.__badmsg = ''
        self.dicClient = {}
        self.__eventManager.start()
        self.EVENT_NEW_CONNECTION = pyevent.Event(
            self.__eventManager, 'EVENT_NEW_CONNECTION')
        self.EVENT_SEND_MESSAGE = pyevent.Event(
            self.__eventManager, 'EVENT_SEND_MESSAGE')
        self.EVENT_RECEIVE_MESSAGE = pyevent.Event(
            self.__eventManager, 'EVENT_RECEIVE_MESSAGE')

    def startListen(self):

        if self.isListening is False:
            if self.__needPrint:
                print('Waiting for connection......')
            thread_listen = threading.Thread(target=self.__listenRecv)
            thread_listen.start()
            return 0
        else:
            if self.__needPrint:
                print('Listener has been started')
            return 1

    def __listenRecv(self):

        self.isListening = True
        while self.isListening:
            try:
                self.__accept()
            except Exception as e:
                print(time.time())
                print(e)

    def __accept(self):

        r_list, _, _ = select.select(
            [self.__socket, ], [], [self.__socket, ], 1)
        for sk in r_list:
            client, addr = sk.accept()
            if self.isListening:
                if self.__needPrint:
                    print('New connection from:', addr)
                t = threading.Thread(target=self.__link, args=(client, addr))
                t.setDaemon(False)
                t.start()
                self.EVENT_NEW_CONNECTION.emit((client, addr))

    def stopListen(self):

        self.isListening = False
        self.__socket.close()
        if self.__needPrint:
            print('Listener has been stoped')

    def __link(self, client, addr):

        while self.isListening:
            recvdata = ''
            try:
                recvdata = client.recv(1024)
                if recvdata:
                    if self.__needfixMixPackets:
                        if recvdata[-6:] == '</a/b>':
                            recvmsg = recvdata.split('</a/b>')
                            if self.__badmsg:
                                piece = self.__badmsg + recvmsg[0]
                                newmsg = piece.split('</a/b>')
                                recvmsg.pop(0)
                                for msg in newmsg[::-1]:
                                    if msg:
                                        recvmsg.insert(0, msg)
                                self.__badmsg = ''
                            for msg in recvmsg:
                                if msg:
                                    self.EVENT_RECEIVE_MESSAGE.emit(
                                        (self, msg, client))
                                    if self.__needPrint:
                                        print('Server receive : "%s"' % msg.replace(
                                            '\r', '\\r').replace('\n', '\\n'))
                        else:
                            recvmsg = recvdata.split('</a/b>')
                            if self.__badmsg:
                                piece = self.__badmsg + recvmsg[0]
                                newmsg = piece.split('</a/b>')
                                recvmsg.pop(0)
                                for msg in newmsg[::-1]:
                                    if msg:
                                        recvmsg.insert(0, msg)
                                self.__badmsg = ''
                            for msg in recvmsg[:-1]:
                                if msg:
                                    self.EVENT_RECEIVE_MESSAGE.emit(
                                        (self, msg, client))
                                    if self.__needPrint:
                                        print('Server receive : "%s"' % msg.replace(
                                            '\r', '\\r').replace('\n', '\\n'))
                            self.__badmsg = recvmsg[-1]
                    else:
                        self.EVENT_RECEIVE_MESSAGE.emit(
                            (self, recvdata, client))
                        if self.__needPrint:
                            print('Server receive : "%s"' % recvdata.replace(
                                '\r', '\\r').replace('\n', '\\n'))
                else:
                    time.sleep(0.001)
            except Exception as e:
                if e.args[0] == 35:
                    time.sleep(0.001)
                    pass
                elif e.args[0] == 54:
                    if self.__needPrint:
                        print('client disconnected:', addr)
                    break
                else:
                    pass

    def sendto(self, client, msg):

        try:
            if self.__needfixMixPackets:
                msgfix = msg + '</a/b>'
            else:
                msgfix = msg
            client.send(msgfix.encode('utf-8'))
            self.EVENT_SEND_MESSAGE.emit((self, msg, client))
            if self.__needPrint:
                print('Server send : "%s"' % msg.replace(
                    '\r', '\\r').replace('\n', '\\n')[:-2])
            return 0
        except Exception:
            return 1


if __name__ == '__main__':

    def myhandler(client, addr):
        print(client, addr)

    server = TcpServer('127.0.0.1', 9981, needPrint=True)
    server.EVENT_NEW_CONNECTION.connectHandler(myhandler)
    server.startListen()
    time.sleep(20)
    server.stopListen()
    print('~~~')
