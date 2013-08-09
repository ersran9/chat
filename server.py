from twisted.internet.protocol.basic import LineReceiver
from twisted.internet.protocol import ServerFactory

class ParseData(object):
    def __init__(self):
        self.dispatch_dict = {'REGISTER': self.register, 'CHAT': self.chat, 'UNREGISTER': self.unregister }
        self.clients = {}

    def dispatch(self, cmd, contents, protocol):
        return dispatch_dict.get(cmd, self.errhandle)(contents, protocol)

    def register(self, contents, protocol):
        """
        REGISTER a new nick to this connection.
        Users cannot talk until they are registered.
        """
        nick = contents.split(':', 1)[0]
        if nick == '' or nick in self.clients:
            return self.errhandle('NICK:Nick already exists. Use another nick')
        
        self.clients[nick] = protocol
        protocol.nick = nick
        protocol.sendLine('OK:NICK:'+protocol.nick)

    def chat(self, contents, protocol):
        """
        CHAT is used to send data to every client connected to server
        """
        if protocol.nick is None:
            return self.errhandle('DATA:Unregistered user! register first.')
        
        for proto in clients.values():
            return self.send(protocol.nick, contents) 

    def unregister(self, contents, protocol):
        """
        UNREGISTER causes the user to be unregistered and disconnected
        """

        if protocol.nick is not None and protocol.nick in self.clients:
            del self.clients[protocol.nick]

        protocol.transport.loseConnection()

    def send(self, nick, contents):
        protocol.sendLine('OK:DATA:'+nick+':'+contents)

    def errhandle(self, message, protocol=None):
        protocol.sendLine('ERR:'+message)
        
class ChatProtocol(LineReceiver):
    nick = None

    def lineReceived(self, line):
        cmd, data = line.split(':',1)
        self.factory.parser.dispatch(cmd, contents, self)

class ChatProtocolFactory(ServerFactory):   
    protocol = ChatProtocol

    def __init__(self):
        self.parser = ParseData()

def main():
    """
    Creates reactor, and adds stuff for making connections
    """

    from twisted import reactor
    p = reactor.listenTCP(int(sys.argv[1]), ChatProtocolFactory(), interface='localhost')
    reactor.run()

if __name__ == '__main__':
    main()
