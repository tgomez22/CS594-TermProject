import socket

class client:
    def __init__(this, name, rooms):
        this.name = name
        this.rooms = rooms

class room:
    def __init__(this, name, clients):
        this.name = name
        this.clients = clients

class server:
    
    def __init__(this):
        # key = client.name, value = client object
        this.clientDictionary = dict({'Testing Steve' : })
        
        # key = room.name, value = room object
        this.roomDictionary = dict({'Waiting Room': })
        
        this.IRC_OPCODE_REGISTER_CLIENT_RESP = 2000
        this.IRC_OPCODE_KEEPALIVE = 2001
        this.IRC_OPCODE_LIST_ROOMS_RESP = 2002
        this.IRC_OPCODE_LIST_USERS_RESP = 2003
        this.IRC_OPCODE_JOIN_ROOM_RESP = 2004
        this.IRC_OPCODE_SEND_MSG = 2005

        this.IRC_ERR = 3000
        this.IRC_ERR_NAME_EXISTS = 3001
        this.IRC_ERR_ILLEGAL_LENGTH = 3002
        this.IRC_ERR_ILLEGAL_OPCODE = 3003
        this.IRC_ERR_ILLEGAL_NAME = 3004
        this.IRC_ERR_ILLEGAL_MESSAGE = 3005
        this.IRC_ERR_TOO_MANY_USERS = 3006
        this.IRC_ERR_TOO_MANY_ROOMS = 3007
        IRC_ERR_RECIPIENT_DOES_NOT_EXIST = 3008
        IRC_ERR_TIMEOUT = 3009

        port = 6667
        host = ''
        welcomeSocket = socket(socket.AF_INET, socket.SOCK_STREAM)
        welcomeSocket.bind()
    
    def registerClient(this, newClient):
        
        if(this.checkIfClientExists(this, newClient) == False):
            this.clientDictionary[newClient.name] = newClient
        else:
            #send back errOpCode to newClient

    def checkIfClientExists(this, potentialClient):
        if potentialClient.name in this.clientDictionary.keys(): 
            return True
        else:
            return False
    
    def sendClientNames(this, requestingClient):
        # send this.clientDictionary.keys() to requestingCLient

    def sendMessageToClient(this, sendingClient, receivingClient, message):
        if (this. checkIfClientExists(this, receivingClient) == True):
            # send message to receivingClient from sendingClient
        else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST
            
            
    def registerRoom(this, newRoom, requestingClient):
        if(this.checkIfRoomExists(this, newRoom) == False)
            this.roomDictionary[newRoom.name] = newRoom
        else: 
            #send room already exists Erno to user.

    def checkIfRoomExists(this, potentialRoom):
        if potentialRoom.name in this.roomDictionary.keys():
            return True
        else:
            return False    

    def sendRoomNames(this, requestingClient):
        # send this.roomDictionary.keys() to requestingClient
        
    def sendMessageToRoom(this, sendingClient, roomName, message):
        if(this.checkIfRoomExists(this, roomName) == True):
            #send message to this.roomDictionary.name from sendingClient
        else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST