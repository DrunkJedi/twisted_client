import binascii

from StringIO import StringIO
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
from smpp.pdu import operations, pdu_types
from smpp.pdu.pdu_encoding import PDUEncoder

from settings import HOST, PORT, LOGIN, PASSWORD


class MyProtocol(Protocol):

    def _bin2pdu(self, bindata):
        io_pdu = StringIO(bindata)
        return PDUEncoder().decode(io_pdu)

    def dataReceived(self, data):
        print 'dataReceived: '
        pdu = self._bin2pdu(data)
        print 'PDU: ', pdu, '\n'

    def connectionMade(self):
        print 'onConnectionMade:', '\n'
        bind_pdu = operations.BindTransmitter(seqNum=1,
                                           system_id=LOGIN,
                                           password=PASSWORD,
                                           system_type='speedflow')

        pdubin = PDUEncoder().encode(bind_pdu)
        self.transport.write(pdubin)

    def connectionLost(self, reason):
        print 'onConnectionLost:'
        print self.transport.realAddress, '\n'


class EchoClientFactory(ClientFactory):

    protocol = MyProtocol

    def startedConnecting(self, connector):
        print 'Started to connect.', '\n'

    def buildProtocol(self, addr):
        p = ClientFactory.buildProtocol(self, addr)
        print 'Connected.'
        print 'protocol', p, '\n'
        return p

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason, '\n'

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason, '\n'


reactor.connectTCP(HOST, PORT, EchoClientFactory())
reactor.run()