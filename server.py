import socket

class client:
    def __init__(this, name):
        this.name = name

class room:
    def __init__(this, name, clients):
        this.name = name
        this.clients = clients #list of clients

class irc_packet:
    opcode = 3000


class server:
    
    def __init__(this):
        # key = client.name, value = client object
        this.clientDictionary = []
        
        this.lobby = room("Lobby", this.clientDictionary)
        # key = room.name, value = room object

        
        this.roomDictionary = dict({lobby.name: lobby})
        
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
        this.IRC_ERR_RECIPIENT_DOES_NOT_EXIST = 3008
        this.IRC_ERR_TIMEOUT = 3009
        this.IRC_ERR_ROOM_DOES_NOT_EXIST = 3010
        this.IRC_ERR_ROOM_ALREADY_EXISTS = 3011

        this.port = 6667
        this.host = ''
        this.welcomeSocket = socket(socket.AF_INET, socket.SOCK_STREAM)
        this.welcomeSocket.bind()
    
    def registerClient(this, newClient):
        if(this.checkIfClientExists(this, newClient) == False):
            this.clientDictionary[newClient.name] = newClient
       # else:
            #send back errOpCode to newClient
            #print("something")

    def checkIfClientExists(this, potentialClient):
        if potentialClient.name in this.clientDictionary.keys(): 
            return True
        else:
            return False

    def addClientToRoom(this, requestingClient:client, requestedRoom:room):
        if (this.checkIfClientExists(this, requestingClient) == True):
            if(this.checkIfRoomExists(requestedRoom) == True):
                this.roomDictionary[requestedRoom.name].clients.append()
            # else: # send IRC_ERR_ROOM_DOES_NOT_EXIST
        #else: #send IRC_ERR and close  connection


    
    def sendClientNames(this, requestingClient:client):
        # send this.clientDictionary.keys() to requestingCLient

    # def sendMessageToClient(this, sendingClient:client, receivingClient:client, message):
       # if (this. checkIfClientExists(this, receivingClient) == True):
            # send message to receivingClient from sendingClient
        #else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST
            
            
    def registerRoom(this, newRoom:room, requestingClient:client):
        if(this.checkIfRoomExists(this, newRoom) == False)
            this.roomDictionary[newRoom.name] = newRoom
       # else: 
            #send room already exists Erno to user. IRC_ERR_ROOM_ALREADY_EXIST

    def checkIfRoomExists(this, potentialRoom:client):
        if potentialRoom.name in this.roomDictionary.keys():
            return True
        else:
            return False    

    def sendAllRoomNames(this, requestingClient:client):
        # send this.roomDictionary.keys() to requestingClient
        
    def sendRoomsForClient(this, requestingClient:client):
        # TODO search client list for each room, and return list of rooms for client


    def sendMessageToRoom(this, sendingClient:client, roomName:room, message):
        if(this.checkIfRoomExists(this, roomName) == True):
            #send message to this.roomDictionary.name from sendingClient
        else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST