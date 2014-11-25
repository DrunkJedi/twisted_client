from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

from settings import HOST, PORT


class MyProtocol(Protocol):

    def dataReceived(self, data):
        print data

    def connectionMade(self):
        print 'onConnectionMade:'
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print 'onConnectionLost:'
        print self.transport.realAddress


class EchoClientFactory(ClientFactory):

    protocol = MyProtocol

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        p = ClientFactory.buildProtocol(self, addr)
        print 'Connected.'
        print 'protocol', p
        return p

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason


reactor.connectTCP(HOST, PORT, EchoClientFactory())
reactor.run()