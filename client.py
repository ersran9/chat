from twisted.internet import stdio, reactor
from twisted.protocols.basic import LineReceiver


class CommandParser(object):
    def __init__(self):
        self.OK_dispatch = {'NICK': self.set_nick, 'CHAT': self.chat, 'UNREGISTER': self.unregister}
    
    def parseIncomingFromServer(self, protocol, prompt, line):
        try:
            status = line.split(':', 1)[0]
            if status == 'ERR':
                return prompt.writeData(line.split(':', 1)[1], err=True)
            cmd = line.split(':', 2)[1]

            self.OK_dispatch.get(cmd, self.errhandle)(protocol, prompt, line.split(':',3)[2])
        except IndexError:
            self.errhandle(protocol, prompt)

    def set_nick(self, protocol, prompt, data):
        protocol.nick = data
        prompt.writeData('Set nick to %s' %(protocol.nick))

    def chat(self. protocol, prompt, data):
        try:
            nick, msg = data.split(':')
        except ValueError:
            self.errhandle(protocol, prompt)
        prompt.writeData('< %s > %s' %(nick, msg))

    def unregister(self, protocol, prompt, data):
        protocol.unreg = True
        protocol.transport.loseConnection()
        prompt.writeData('Connection with server %s closed.' %(protocol.transport.getPeer()))

    def errhandle(self, protocol, prompt, msg=None):
        if msg:
            prompt.writeData(msg, err=True)
        else:
            prompt.writeData("Something has gone wrong. Don't worry, carry on with your talk", err=True)
            
class CommandPrompt(LineReceiver):
    from os import linesep as delimiter

    def connectionMade(self):
        self.sendLine('[OK] Connected to shell. Welcome to The chat application!')

    def lineReceived(self, line):
        if 'NICK' in line:
            try:
                cmd, data = line.split(':', 1)
                if not cmd == 'NICK':
                    raise ValueError

                return self.factory.protocol_instance.sendLine('REGISTER:%s' %(data.lstrip().rstrip()))
            except ValueError:
                pass

        if 'QUIT' in line:
            try:
                cmd = line.strip()
                if cmd == 'QUIT':
                    return self.factory.protocol_instance.sendLine('UNREGISTER:')
            except ValueError:
                pass

        self.factory.protocol_instance.sendLine('CHAT:'+line)

    def writeData(self, line, err=None):
        if err:
            status = 'ERROR'
        else:
            status = 'OK'
        self.sendLine('['+status+'] ' + line)
    

class ChatProtocol(LineReceiver):
    
    def __init__(self):
        self.nick = None

    def connectionMade(self):
        self.factory.prompt.writeData('Connected to server at: %s ', self.transport.getPeer())

    def connectionLost(self):
        if self.unreg:
            return
        self.factory.prompt.writeData('Lost connection to server at: %s ', self.transport.getPeer()) 

    def LineReceived(self, line):
        self.factory.cmdparser.parseIncomingFromServer(self, self.factory.cmd, line)

class ChatProtocolFactory(ClientFactory):

    protocol = ChatProtocol

    def __init__(self):
        self.cmdparser = CommandLineParser()
        self.cmd = CommandPrompt()

    def buildProtocol(self, addr):
        protocol = ClientFactory.buildProtocol(self, addr)
        self.protocol_instance = protocol
        return protocol

def main():
    """
    Creates reactor, adds stuff for listening to STDIO 
    """

    from twisted.internet import reactor
    import sys
    
    factory = ChatProtocolFactory()
    cmdprompt = CommandPrompt()
    factory.cmd = cmdprompt
    reactor.connectTCP(sys.argv[1], int(sys.argv[2]), ChatProtocolFactory())
    stdio.StandardIO(cmdprompt)
    reactor.run()

if __name__ == '__main__':
    main()
