# -*- coding: utf-8 -*-

from StringIO import StringIO
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, task
from smpp.pdu import operations
from smpp.pdu.pdu_encoding import PDUEncoder

from settings import HOST, PORT, LOGIN, PASSWORD, SMSCOUNT


class MyProtocol(Protocol):
    def dataReceived(self, data):
        pdu = self._bin2pdu(data)
        if str(pdu.commandId) == 'submit_sm_resp':
            self.SMSSUBMITTED = self.SMSSUBMITTED + 1
            print 'submit_sm_resp: ', self.SMSSUBMITTED
            if SMSCOUNT == self.SMSSUBMITTED:
                self._unbind()
        elif str(pdu.commandId) == 'bind_transmitter_resp' and str(pdu.status) == 'ESME_ROK':
            print 'Auth OK'
            self.state = 'BINDED'
            self.SMSSUBMITTED = 0
            self.SMSSENDED = 0
            self.send_sms = task.LoopingCall(self._submit_sm)
            self.send_sms.start(0.01)
        elif str(pdu.status) == 'ESME_RINVSYSID':
            print 'Invalid System ID'

    def connectionMade(self):
        self.state = 'BINDING'
        self._bind()

    def connectionLost(self, reason):
        print 'onConnectionLost:'
        print self.transport.realAddress, '\n'
        if self.state == 'UNBINDING':
            print 'Unbinding done'

    def _bin2pdu(self, bindata):
        io_pdu = StringIO(bindata)
        return PDUEncoder().decode(io_pdu)

    def _pdu2bin(self, bindata):
        return PDUEncoder().encode(bindata)

    def _submit_sm(self):
        if SMSCOUNT != self.SMSSENDED:
            seq_num = self.SMSSENDED + 1
            print 'Submit sm: ', seq_num
            message_text = "This is MESSAGE!!1" + str(seq_num)
            sm_pdu = operations.SubmitSM(
                seqNum=seq_num,
                short_message=message_text,
                destination_addr='380660803034',
            )
            pdubin = self._pdu2bin(sm_pdu)
            self.transport.write(pdubin)
            self.SMSSENDED = seq_num
        else:
            self.send_sms.stop()

    def _enqire_link(self):
        print 'Sending enqirelink start\n'
        enqlink = operations.EnquireLink(
            seqNum=1
        )
        enqlink = self._pdu2bin(enqlink)
        self.transport.write(enqlink)
        print 'Sending enqirelink done\n'

    def _unbind(self):
        print 'Unbinding start'
        self.state = 'UNBINDING'
        unbind = operations.Unbind(
            seqNum=1
        )
        unbind = self._pdu2bin(unbind)
        self.transport.write(unbind)

    def _bind(self):
        bind_pdu = operations.BindTransmitter(seqNum=1,
                                              system_id=LOGIN,
                                              password=PASSWORD,
                                              system_type='speedflow')
        pdubin = self._pdu2bin(bind_pdu)
        self.transport.write(pdubin)


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