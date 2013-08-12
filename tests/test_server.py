from chat.server import ChatProtocolFactory
from twisted.test import proto_helpers
from twisted.trial import unittest


class ChatServerTest(unittest.TestCase):
    """
    Tests for the Chat Server follows
    """

    def setUp(self):
        factory = ChatProtocolFactory()
        self.proto1 = factory.buildProtocol(('127.0.0.1', 0))
        self.proto2 = factory.buildProtocol(('127.0.0.1', 0))
        self.proto3 = factory.buildProtocol(('127.0.0.1', 0))

        self.proto1.factory = factory
        self.proto2.factory = factory
        self.proto3.factory = factory 

        self.tr1 = proto_helpers.StringTransport()
        self.tr2 = proto_helpers.StringTransport()
        self.tr3 = proto_helpers.StringTransport()

        self.proto1.makeConnection(self.tr1)
        self.proto2.makeConnection(self.tr2)
        self.proto3.makeConnection(self.tr3)
    
    def tearDown(self):
        self.proto1.transport.loseConnection()
        self.proto2.transport.loseConnection()
        self.proto3.transport.loseConnection()

    def test_register(self):
        """
        Tests the REGISTER command of chat. Used to 'add' the user to the chat
        command is of the format REGISTER:<NICK>:<NULL>
        Reply is in the format: 
        1. If success then -> OK:NICK:<NICK>
        2. If failed then ->  ERR:NICK:<MSG>
        """

        self.proto1.lineReceived('REGISTER:foo:')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), ['foo'])
        self.assertEqual(self.tr1.value().strip(), 'OK:NICK:foo')

        self.proto2.lineReceived('REGISTER:foo:')
        self.assertEqual(self.tr2.value().strip(), 'ERR:NICK:Nick already exists. Use another nick')

        self.proto3.lineReceived('REGISTER:bar:')
        self.assertItemsEqual(self.proto3.factory.parser.get_clients(), ['foo', 'bar'])
        self.assertEqual(self.tr3.value().strip(), 'OK:NICK:bar')

    def test_valid_chat(self):
        """
        Tests the CHAT command of chat. Used by users to send their data to server
        Server will then send the data to all clients.
        command is of the format CHAT:<DATA>
        Reply for success is in the format -> OK:DATA:<NICK>:<MESSAGE>
        """
        
        self.proto1.lineReceived('REGISTER:foo:')
        self.proto1.lineReceived('CHAT:This is a test message')
        self.assertEqual(self.tr1.value().strip(), 'OK:NICK:foo\r\nOK:CHAT:foo:This is a test message')

    def test_invalid_chat(self):
        """
        Test the CHAT command when the user has not actually registered themselves
        """
        
        self.proto1.lineReceived('CHAT:foo:This is a test message')
        self.assertEqual(self.tr1.value().strip(), 'ERR:CHAT:Unregistered user! register first.')

    def test_unregister(self):
        """
        Tests the UNREGISTER command of chat. Used to unregister and remove the connection
        Command is of the format UNREGISTER::
        No reply is there for this command
        """

        self.proto1.lineReceived('REGISTER:foo:')
        self.assertEqual(self.tr1.value().strip(), 'OK:NICK:foo')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), ['foo'])
        self.proto1.lineReceived('UNREGISTER::')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), [])

        # if someone unregistered sends unregister, ignore them
        self.proto1.lineReceived('UNREGISTER::')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), [])

    def test_change_nick(self):
        """
        Tests whether on changing nick, proper updation is done at server side
        """
        self.proto1.lineReceived('REGISTER:foo:')
        self.proto1.lineReceived('CHAT:hey')
        self.proto1.lineReceived('REGISTER:bar:')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), ['bar'])
        self.assertEqual(self.tr1.value().strip(), 'OK:NICK:foo\r\nOK:CHAT:foo:hey\r\nOK:NICK:bar')
    
    def test_unregistered_user(self):
        """
        Tests that an unregistered user is not allowed to talk
        """

        self.proto1.lineReceived('CHAT:what up buddy?')
        self.assertEqual(self.tr1.value().strip(), 'ERR:CHAT:Unregistered user! register first.')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), [])

    def test_user_disconnected(self):
        """
        Tests that when user is disconnected, proper cleanup is performed
        """
        self.proto1.lineReceived('REGISTER:foo:')
        self.proto1.lineReceived('CHAT:hey')
        self.proto1.lineReceived('UNREGISTER:')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), [])

    def test_get_clients(self):
        """
        Tests the get_clients method of parser
        """
        self.proto1.lineReceived('REGISTER:foo:')
        self.proto2.lineReceived('REGISTER:bar:')
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), self.proto1.factory.parser.clients.keys())

    def test_invalid_data(self):
        """
        Tests that server ignores invalid data
        """
         
        self.proto1.lineReceived('REGISTER:foo:')
        self.proto1.lineReceived('hahahahahhahahahhahahahahhaa')
        self.proto1.lineReceived('muahahahhahahahahhahahahahah')
        self.assertEqual(self.tr1.value(), 'OK:NICK:foo\r\n')


        self.proto2.lineReceived('REGISTER:soo:')
        self.proto2.lineReceived('hahahahahhahahahhahahahahha:a')
        self.proto2.lineReceived('muahahahhahahahahhahahaha:hah')
        self.assertEqual(self.tr2.value(), 'OK:NICK:soo\r\nERR:a\r\nERR:hah\r\n')

    def test_connection_lost(self):
        """
        Tests that when connection is lost, reuse of nick is allowed
        """

        self.proto1.lineReceived('REGISTER:foo:')
        self.proto1.lineReceived('CHAT: ok some data')
        self.proto1.loseConnection()
        self.assertItemsEqual(self.proto1.factory.parser.get_clients(), [])
        self.proto2.lineReceived('REGISTER:foo:')
        self.assertEqual(self.tr2.value().strip(), 'OK:NICK:foo')
