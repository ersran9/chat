chat
====
Chat server and client - written in python with twisted.
reason
======
**why the heck did you create yet another stupid protocol?** Because I wanted to learn twisted, nothing else.
I do realize that introducing a new protocol isn't going to solve anything - this is just an attempt to 
understand how stuff works with twisted.
status
======
The server works as of now - there's a test suite that covers most of the functionality. Use it as

`python server.py <port>`

server - commands accepted
==========================
The server accepts the following commands

1. `REGISTER:<NICK>:` - registers a new nick and enables the user to talk
2. `CHAT:<DATA>:` - send <DATA> data to other people connected
3. `UNREGISTER:` - disconnects the user






