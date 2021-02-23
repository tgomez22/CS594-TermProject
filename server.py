import socket
import irc_protocol
import pickle

from _thread import *

#TODO 
class room:
    def __init__(self, name, clients):
        self.name = name
        self.clients = clients #list of clients

class irc_packet:
    opcode = 3000


class server:
    
    def __init__(self):
        #list of all clients connected to server
        self.clientList = [] 
        
        # key = roomName, value = list of clients joined in room
        self.roomDictionary = {"Lobby":[]}
        self.name = "Tristan and Lydia's IRC Server"
        self.host = '127.0.0.1'
        self.port = 6667
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.threadCount = 0
        self.buffSize = 4096
        
    def threaded_client(self, connection):
        connection.send(str.encode('Welcome to Tristan and Lydia\'s IRC Server!\n'))
        while True:
            data = connection.recv(self.buffSize)
            clientRegisterRequestPacket = pickle.loads(data)

            print(f"\n\nclientRegisterRequestPacket type: {type(clientRegisterRequestPacket)}\n\n")

            registerResponsePacket = self.handlePacket(clientRegisterRequestPacket)
            if not clientRegisterRequestPacket:
                break
            connection.sendall(pickle.dumps(registerResponsePacket))
        connection.close()

    def startServer(self):
        try:
            self.serverSocket.bind((self.host, self.port))
        except socket.error as e:
            print(str(e))      

        print('Waiting for a Connection...\n')
        self.serverSocket.listen(5)

        while True:
            client, address = self.serverSocket.accept()
            print(f'Connected to: {address[0]}: {str(address[1])}')
            start_new_thread(self.threaded_client, (client, ))
            self.threadCount += 1
            print(f'Thread number: {str(self.threadCount)}')
        self.serverSocket.close()

    def registerClient(self, newClient):
        #check if legal name
        if(len(newClient) < 1 or len(newClient) > 32 or newClient.startswith(' ') or newClient.endswith(' ')):
            return irc_protocol.ircOpcodes.IRC_ERR_ILLEGAL_NAME
        for letter in newClient:
            if(ord(letter) < 32 or ord(letter) > 126):
                return irc_protocol.ircOpcodes.IRC_ERR_ILLEGAL_NAME
        
        if newClient in self.clientList:
            return irc_protocol.ircOpcodes.IRC_ERR_NAME_EXISTS
        else:
            if newClient in self.roomDictionary.keys():
                return irc_protocol.ircOpcodes.IRC_ERR_NAME_EXISTS
            else:    
                self.clientList.append(newClient)
                return irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_RESP

    def addClientToRoom(self, requestingClient, requestedRoom):

        #if client exists
        if requestingClient in self.clientList:

            #if room exists
            if requestedRoom in roomDictionary.keys():

                #client is not already in room
                if not requestingClient in roomDictionary[requestedRoom]:

                    #if room can handle more users 
                    if(len(self.roomDictionary[requestedRoom]) < 100):
                        self.roomDictionary[requestedRoom].clients.append()
                        return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP, 0), "")

                    #if room is full
                    else:
                        return ircPacket(ircHeader(ircOpcodes.IRC_ERR_TOO_MANY_USERS, 0), "")

                #client IS in room
                else:
                    return ircPacket(ircHeader(ircOpcodes.IRC_ERR_USER_ALREADY_IN_ROOM, 0), "")
                    
            #room doesn't exist
            else:
                return ircPacket(ircHeader(ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST, 0), "") 
        
        else: 
            #do we need CLOSE CONNECTION functionality here???
            return ircPacket(ircHeader(ircOpcodes.IRC_ERR, 0), "")


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

        
    # def sendRoomsForClient(self, requestingClient):
    #     roomList = []
    #     for roomName in self.roomDictionary.keys():
    #         if requestingClient in roomDictionary[roomName].values():
    #             roomList.append(room.)
        # TODO search client list for each room, and return list of rooms for client


    # def sendMessageToRoom(self, sendingClient, roomName:room, message):
    #     if roomName in self.roomDictionary.keys():
    #         #send message to self.roomDictionary.name from sendingClient
    #     else:
            # send IRC_ERR_RECIPIENT_DOES_NOT_EXIST

    def handlePacket(self, packet: irc_protocol.ircPacket):
        print(f"\npacket type: {type(packet)}\n")


        #register new client
        if(packet.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ):
            regClientHeader = irc_protocol.ircHeader(self.registerClient(packet.payload), 0)
            return irc_protocol.ircPacket(regClientHeader, "")
            
        #list rooms request
        elif packet.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ:
            return irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP, len(self.roomDictionary.keys())), self.roomDictionary.keys())
            # in payload
            
        #list users request
        elif(packet.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_REQ):
            return irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_RESP, len(self.clientList)), self.clientList)

        #join room request
        elif packet.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_REQ:
            return self.addClientToRoom(packet.payload.senderName, packet.payload.content)    
        
        #send message
      #  elif(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_SEND_MSG_REQ):
       #     if ():




testServer = server()
testServer.startServer()
    