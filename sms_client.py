# -*- coding: utf-8 -*-
import binascii
import chardet

from StringIO import StringIO
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
from smpp.pdu import operations, pdu_types
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
            for i in range(1, SMSCOUNT + 1):
                print 'sebmit_sm', i
                self._submit_sm(i)
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

    def _submit_sm(self, seq_num=1):
        message_text = "This is MESSAGE!!1"
        encoding = chardet.detect(message_text)['encoding']
        data_coding = pdu_types.DataCoding(
            scheme=pdu_types.DataCodingScheme.DEFAULT,
            schemeData=pdu_types.DataCodingDefault.UCS2
        )
        message_text = message_text.decode(encoding).encode('utf-16-be')
        sm_pdu = operations.SubmitSM(
            seqNum=seq_num,
            short_message=message_text,
            # destination_addr='380669113263', #sasha
            #destination_addr='380930188472', #kiril
            # destination_addr='380632588588',
            destination_addr='380660803034',  #sergey
            #destination_addr='380977927149',  # igor
            source_addr_ton=pdu_types.AddrTon.ALPHANUMERIC,
            source_addr_npi=pdu_types.AddrNpi.UNKNOWN,
            source_addr='380632588588',
            dest_addr_ton=pdu_types.AddrTon.INTERNATIONAL,
            dest_addr_npi=pdu_types.AddrNpi.ISDN,
            data_coding=data_coding,
            registered_delivery=pdu_types.RegisteredDelivery(
                pdu_types.RegisteredDeliveryReceipt.SMSC_DELIVERY_RECEIPT_REQUESTED)
        )

        pdubin = PDUEncoder().encode(sm_pdu)

        hex_stream = '00000071000000040000000000005b73000500496e666f0001013338303933333033303737370003000000303030303031303030303030303030520001000800300414043e0431044004380439002004340435043d044c00200021002004420435044104420020041f043004320435043b'
        pdubin = binascii.a2b_hex(hex_stream)

        self.transport.write(pdubin)

    def _enqire_link(self):
        print 'Sending enqirelink start\n'
        enqlink = operations.EnquireLink(
            seqNum=1
        )
        enqlink = PDUEncoder().encode(enqlink)
        self.transport.write(enqlink)
        print 'Sending enqirelink done\n'

    def _unbind(self):
        print 'Unbinding start'
        self.state = 'UNBINDING'
        unbind = operations.Unbind(
            seqNum=1
        )
        unbind = PDUEncoder().encode(unbind)
        self.transport.write(unbind)

    def _bind(self):
        bind_pdu = operations.BindTransmitter(seqNum=1,
                                              system_id=LOGIN,
                                              password=PASSWORD,
                                              system_type='speedflow')
        pdubin = PDUEncoder().encode(bind_pdu)
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