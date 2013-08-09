from chat.server import ChatProtocolFactory
from twisted.trial import unittest
from twisted.test import proto_helpers

class ChatServerTest(unittest):
    """
    Tests for the Chat Server follows
    """

    def setUp(self):
        factory = ChatProtocolFactory()
        self.proto1 = factory.buildProtocol(('127.0.0.1', 0))
        self.proto2 = factory.buildProtocol(('127.0.0.1', 0))
        self.proto3 = factory.buildProtocol(('127.0.0.1', 0))

        self.tr1 = proto_helpers.StringTransport()
        self.tr2 = proto_helpers.StringTransport()
        self.tr3 = proto_helpers.StringTransport()

        self.proto1.makeConnection(self.tr1)
        self.proto2.makeConnection(self.tr2)
        self.proto3.makeConnection(self.tr3)
       
    def test_register(self):
        """
        Tests the REGISTER command of chat. Used to 'add' the user to the chat
        command is of the format REGISTER:<NICK>:<NULL>
        Reply is in the format: 
        1. If success then -> OK:NICK:<NICK>
        2. If failed then ->  ERR:NICK:<MSG>
        """

        self.proto1.dataReceived('REGISTER:foo:')
        self.assertItemsEqual(factory.get_clients(), set(['foo']))
        self.assertEqual(self.tr1.value(), 'OK:NICK:foo')

        self.proto2.dataReceived('REGISTER:foo:')
        self.assertEqual(self.tr2.value(), 'ERR:NICK:Nick already exists. Use another nick')

        self.proto3.dataReceived('REGISTER:bar:')
        self.assertItemsEqual(factory.get_clients(), set(['foo', 'bar']))
        self.assertEqual(self.tr2.value(), 'OK:NICK:bar')

    def test_valid_chat(self):
        """
        Tests the CHAT command of chat. Used by users to send their data to server
        Server will then send the data to all clients.
        command is of the format CHAT:<DATA>
        Reply for success is in the format -> OK:DATA:<NICK>:<MESSAGE>
        """
        
        self.proto1.dataReceived('REGISTER:foo:')
        self.assertEqual(self.tr1.value(), 'OK:NICK:foo')
        self.proto1.dataReceived('CHAT:foo:This is a test message')
        self.assertEqual(self.tr1.value(), 'OK:DATA:foo:This is a test message')
        self.assertEqual(self.tr2.value(), 'OK:DATA:foo:This is a test message')
        self.assertEqual(self.tr3.value(), 'OK:DATA:foo:This is a test message')

    def test_invalid_chat(self):
        """
        Test the CHAT command when the user has not actually registered themselves
        """
        
        self.proto1.dataReceived('CHAT:foo:This is a test message')
        self.assertEqual(self.tr1.value(), 'ERR:DATA:Unregistered user! register first.')

    def test_unregister(self):
        """
        Tests the UNREGISTER command of chat. Used to unregister and remove the connection
        Command is of the format UNREGISTER::
        No reply is there for this command
        """

        self.proto1.dataReceived('REGISTER:foo:')
        self.assertEqual(self.tr1.value(), 'OK:NICK:foo')
        self.assertItemsEqual(factory.get_clients(), set(['foo']))
        self.proto1.dataReceived('UNREGISTER::')
        self.assertItemsEqual(factory.get_clients(), set())

        # if someone unregistered sends unregister, ignore them
        self.proto1.dataReceived('UNREGISTER::')
        self.assertItemsEqual(factory.get_clients(), set())

