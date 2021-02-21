import socket
import irc_protocol

#TODO 
class room:
    def __init__(self, name, clients):
        self.name = name
        self.clients = clients #list of clients

class irc_packet:
    opcode = 3000


class server:
    
    def __init__(self):
        self.clientList = []
        
        self.lobby = room("Lobby", self.clientList)
        
        # key = room.name, value = room object
        self.roomDictionary = dict({lobby.name: lobby})
        
        self.port = 6667
        self.host = ''
        self.welcomeSocket = socket(socket.AF_INET, socket.SOCK_STREAM)
        self.welcomeSocket.bind()
    
    def registerClient(self, newClient):
        #check if legal name
        if(len(newClient) < 1 or len(newClient) > 32 or newClient.startswith(' ') or newClient.endswith(' ')):
            return ircOpcodes.IRC_ERR_ILLEGAL_NAME
        for letter in newClient:
            if(ord(letter) < 32 or ord(letter) > 126):
                return ircOpcodes.IRC_ERR_ILLEGAL_NAME
        
        if newClient in self.clientList:
            return ircOpcodes.IRC_ERR_NAME_EXISTS
        else:
            if newClient in roomDictionary.keys():
                return ircOpcodes.IRC_ERR_NAME_EXISTS
            else:    
                self.clientList.append(newClient)
                return ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_RESP

    def addClientToRoom(self, requestingClient, requestedRoom):

        #if client exists
        if requestingClient in self.clientList:

            #if room exists
            if requestedRoom in roomDictionary.keys():

                #if room can handle more users
                if(len(self.roomDictionary[requestedRoom]) < 100):
                    self.roomDictionary[requestedRoom].clients.append()
                    return ircPacket(header(ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP, 0), "")

                #if room is full
                else:
                    return ircPacket(header(ircOpcodes.IRC_ERR_TOO_MANY_USERS, 0), "")
            
            #room doesn't exist
            else:
                return ircPacket(header(ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST, 0), "") 
        
        else: 
            #do we need CLOSE CONNECTION functionality here???
            return ircPacket(header(ircOpcodes.IRC_ERR, 0), "")


    # def sendMessageToClient(self, sendingClient:client, receivingClient:client, message):
       # if (self. checkIfClientExists(self, receivingClient) == True):
            # send message to receivingClient from sendingClient
        #else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST
            
            
    def registerRoom(self, newRoom:room, requestingClient):
        if newRoom in roomDictionary.keys():
            #send room already exists Erno to user. IRC_ERR_ROOM_ALREADY_EXIST
            return
        else: 
            self.roomDictionary[newRoom.name] = newRoom


    def sendAllRoomNames(self, requestingClient):
        # send self.roomDictionary.keys() to requestingClient
        
    def sendRoomsForClient(self, requestingClient):
        # TODO search client list for each room, and return list of rooms for client


    def sendMessageToRoom(self, sendingClient, roomName:room, message):
        if roomName in self.roomDictionary.keys():
            #send message to self.roomDictionary.name from sendingClient
        else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST

    def handlePacket(self, packet: ircPacket):
        
        #register new client
        if(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ):
            return ircPacket(ircHeader(self.registerClient(ircPacket.payload.senderName), 0) "")
            
        #list rooms request
        elif(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ):
            return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP, len(self.roomDictionary.keys()), self.roomDictionary.keys())  # in payload
            
        #list users request
        elif(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_LIST_USERS_REQ):
            return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_LIST_USERS_RESP, len(self.clientList)), self.clientList)

        #join room request
        elif(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_JOIN_ROOM_REQ):
            return self.addClientToRoom(ircPacket.payload.senderName, ircPacket.payload.content)    
        
        #send message
        elif(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_SEND_MSG_REQ):
            if ():
