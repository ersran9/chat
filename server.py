from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ServerFactory

class ParseData(object):
    def __init__(self):
        self.dispatch_dict = {'REGISTER': self.register, 'CHAT': self.chat, 'UNREGISTER': self.unregister }
        self.clients = {}

    def dispatch(self, cmd, contents, protocol):
        return self.dispatch_dict.get(cmd, self.errhandle)(contents, protocol)

    def register(self, contents, protocol):
        """
        REGISTER a new nick to this connection.
        Users cannot talk until they are registered.
        """
        nick = contents.split(':', 1)[0]
        if nick == '' or nick in self.clients:
            return self.errhandle('NICK:Nick already exists. Use another nick', protocol)
        
        for nick_, protocol_ in self.clients.items():
            if protocol_ == protocol:
                del self.clients[nick]
                self.clients[nick_] = protocol
                return protocol.sendLine('OK:NICK:'+protocol.nick)

        self.clients[nick] = protocol
        protocol.nick = nick
        protocol.sendLine('OK:NICK:'+protocol.nick)

    def chat(self, contents, protocol):
        """
        CHAT is used to send data to every client connected to server
        """
        if protocol.nick is None:
            return self.errhandle('CHAT:Unregistered user! register first.', protocol)
        
        for proto in self.clients.values():
            self.send(proto, protocol.nick, contents) 

    def unregister(self, contents, protocol):
        """
        UNREGISTER causes the user to be unregistered and disconnected
        """
        if protocol.nick is not None and protocol.nick in self.clients:
            del self.clients[protocol.nick]

        protocol.transport.loseConnection()

    def send(self, protocol, nick, contents):
        protocol.sendLine('OK:CHAT:'+nick+':'+contents)

    def errhandle(self, message, protocol):
        protocol.sendLine('ERR:'+message)

    def get_clients(self):
        return self.clients.keys()
        
class ChatProtocol(LineReceiver):
    nick = None

    def lineReceived(self, line):
        cmd, data = line.split(':',1)
        self.factory.parser.dispatch(cmd, data, self)

    def connectionLost(self, reason):
        """
        perform cleanup here. entries made in client dict are to be cleared out
        [ in ParseData class ]
        """
        for nick, protocol in self.factory.parser.clients:
            if self == protocol:
                del self.factory.parser.clients[nick]
                return
        
class ChatProtocolFactory(ServerFactory):   
    protocol = ChatProtocol

    def __init__(self):
        self.parser = ParseData()

def main():
    """
    runs reactor, and adds stuff for making connections
    """

    from twisted.internet import reactor
    import sys
    p = reactor.listenTCP(int(sys.argv[1]), ChatProtocolFactory(), interface='localhost')
    reactor.run()

if __name__ == '__main__':
    main()
