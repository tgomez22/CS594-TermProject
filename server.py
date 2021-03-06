
import socket
import pickle
from irc_protocol import *
from _thread import *
import threading


class server:

    def __init__(self):

        # key = name, value = socket for the
        self.clientDictionary = {}

        # key = roomName, value = list of clients joined in room
        self.roomDictionary = {"Lobby": []}
        self.name = "Tristan and Lydia's IRC Server"
        self.host = '127.0.0.1'
        self.port = 6667
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # socket.create_server((host, port))
        self.threadCount = 0
        self.buffSize = 4096
        self.mutex = threading.Lock()


    

    def threadedClient(self, connection, address):
        connection.send(str.encode(
            'Welcome to Tristan and Lydia\'s IRC Server!\n'))
        clientAlive = True
        while clientAlive == True:
            try:
                data = connection.recv(self.buffSize)
            except:
                print("\n*** ERROR Detected ***")
                self.mutex.acquire()
                clientInDictionary = None
                for client, value in self.clientDictionary.items():
                    if value == connection:
                        clientInDictionary = client

                if clientInDictionary != None:
                    print(f"clients beofre removing {clientInDictionary} from connected clients:\n{self.clientDictionary}")
                    # self.clientDictionary.pop(clientInDictionary)
                    del self.clientDictionary[clientInDictionary]
                    print(f"After {clientInDictionary} was removed: ")
                    print(self.clientDictionary)

                roomsClientIsIn = []
                for room, members in self.roomDictionary.items():
                    for member in list(members):
                        if member == client:
                            roomsClientIsIn.append(room)


                if len(roomsClientIsIn) > 0:
                    for room in roomsClientIsIn:
                        self.roomDictionary[room].remove(client)
                        print(f"{client} removed from room: {room}")

                self.mutex.release()
                self.threadCount -= 1
                return
            if not data:
                break

            clientRequestPacket = pickle.loads(data)

            responsePacket = self.handlePacket(clientRequestPacket, connection)
            if(responsePacket == None):
                clientAlive = False
            else:
                try:
                    connection.send(pickle.dumps(responsePacket))
                except:
                    print("Cannot send data")
                    break
        connection.close()
        print(f"Connection closed on address {address}\n")
        self.threadCount -= 1

    def startServer(self):
        try:
            self.serverSocket.bind((self.host, self.port))
            print('Waiting for a Connection...\n')
            self.serverSocket.listen(25)  # have up to 25 connections
        except socket.error as e:
            print(str(e))

        while True:
            client, address = self.serverSocket.accept()

            print(f'Connected to: {address[0]}: {str(address[1])}')
            
            self.threadCount += 1
            print(f'\nThread Number: {str(self.threadCount)}')
            print(f'active threads: {threading.active_count}')

            start_new_thread(self.threadedClient, (client, address))

        self.serverSocket.close()

    def isNameLegal(self, name: str):
        if(len(name) < 1 or len(name) > 32 or name.startswith(' ') or name.endswith(' ')):
            return False
        for letter in name:
            if(ord(letter) < 32 or ord(letter) > 126):
                return False
        return True

    def registerClient(self, newClient, connection):
        # check if legal name
        print(f"\nChecking if {newClient} is a legal name...")
        if not self.isNameLegal(newClient):
            print(f"ERROR: name contains illegal characters: {newClient}")
            return ircOpcodes.IRC_ERR_ILLEGAL_NAME

        print(f"Checking if {newClient} is already taken name...")
        self.mutex.acquire()
        if newClient in list(self.clientDictionary.keys()):
            print(f"ERROR: Name already taken: {newClient} ")


            self.mutex.release()
            return ircOpcodes.IRC_ERR_NAME_EXISTS
        else:
            print(f"Client being added to server with name:{newClient}")
            self.clientDictionary[newClient] = connection

            print(f"\nList of all clients connected")
            for client in list(self.clientDictionary.keys()):
                print(f"  - {client}")

            print("\nList of clients currently in Lobby:")
            self.roomDictionary["Lobby"].append(newClient)
            for client in list(self.roomDictionary["Lobby"]):
                print(f" - {client}")
            self.mutex.release()

            return ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_RESP

    def addClientToRoom(self, requestingClient, requestedRoom):
        self.mutex.acquire()
        # if client exists
        if requestingClient in list(self.clientDictionary.keys()):

            # if room exists
            if requestedRoom in list(self.roomDictionary.keys()):

                # client is not already in room
                if not requestingClient in self.roomDictionary[requestedRoom]:

                    # if room can handle more users
                    if(len(self.roomDictionary[requestedRoom]) < 100):
                        self.roomDictionary[requestedRoom].append(
                            requestingClient)
                        self.mutex.release()
                        return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP, 0), "")

                    # if room is full
                    else:
                        self.mutex.release()
                        return ircPacket(ircHeader(ircOpcodes.IRC_ERR_TOO_MANY_USERS, 0), "")

                # client IS in room
                else:
                    self.mutex.release()
                    return ircPacket(ircHeader(ircOpcodes.IRC_ERR_USER_ALREADY_IN_ROOM, 0), "")

            # room doesn't exist
            else:
                self.mutex.release()
                return ircPacket(ircHeader(ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST, 0), "")

        else:
            # do we need CLOSE CONNECTION functionality here???
            self.mutex.release()
            return ircPacket(ircHeader(ircOpcodes.IRC_ERR, 0), "")

    def makeNewRoom(self, packet):
        newRoom = packet.payload.roomName
        # room exits return err
        self.mutex.acquire()
        if newRoom in list(self.roomDictionary.keys()):
            self.mutex.release()
            return ircOpcodes.IRC_ERR_ROOM_ALREADY_EXISTS
        # illegal room name, return err
        elif not self.isNameLegal(newRoom):
            self.mutex.release()
            return ircOpcodes.IRC_ERR_ILLEGAL_NAME
        # valid room name, create room
        else:
            self.roomDictionary[packet.payload.roomName] = [
                packet.payload.senderName]
            self.mutex.release()
            return ircOpcodes.IRC_OPCODE_MAKE_ROOM_RESP

    def forwardMessageToRoom(self, packet: ircPacket):
        room = packet.payload.receiverName
        sender = packet.payload.message.senderName
        message = packet.payload.message.messageBody
        print(f"\n forwarding message to room: {room} from {sender}")
        print(f"message:{message}")

        for client in list(self.roomDictionary[room]):
            if client != sender:
                print(f"forwarding to client {client}")
               # packet.payload.receiverName = client
               # packet.header.payloadLength = len(room) + len(sender) + len(message) + len(client)
                self.forwardMessageToClient(client, packet)

        # ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_SEND_MSG_RESP, payloadLength), packet.payload)

    def forwardMessageToClient(self,client, packet: ircPacket):
       # lengthSenderName = len(packet.payload.message.senderName)
       # receiverName = packet.payload.receiverName
       # lengthMessage = len(packet.payload.message.messageBody)
        #payloadLength = lengthSenderName + lengthMessage

        packet.header.opCode = ircOpcodes.IRC_OPCODE_FORWARD_MESSAGE
        # forwardHeader = ircHeader(
        #     ircOpcodes.IRC_OPCODE_FORWARD_MESSAGE, payloadLength)
        # forwardPacket = ircPacket(forwardHeader, packet.payload)
        try:
            self.mutex.acquire()
            self.clientDictionary[client].send(
                pickle.dumps(packet))
            self.mutex.release()
        except socket.error as e:
            print(str(e))


    def sendMessageRequest(self, packet: ircPacket):
        if packet.payload.receiverName not in (self.roomDictionary.keys()):
            return ircPacket(ircHeader(ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST, 0), "")
        else:
            print(f"\nReceived request to send message")
            print(f"sender name: {packet.payload.message.senderName}")
            print(f"recipient name: {packet.payload.receiverName}")
            start_new_thread(self.forwardMessageToRoom, (packet, ))
            messageLen = len(packet.payload.message.messageBody)
            roomNameLength = len(packet.payload.receiverName)
            senderNameLength = len(packet.payload.message.senderName)
            packetLength = messageLen + roomNameLength + senderNameLength
            return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_SEND_MSG_RESP, packetLength), packet.payload)

    def getMembersOfSpecificRoom(self, desiredRoom):
        self.mutex.acquire()
        if desiredRoom not in list(self.roomDictionary.keys()):
            self.mutex.release()
            return ircPacket(ircHeader(ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST), "")
        else:
            responsePayload = list(self.roomDictionary[desiredRoom])
            responseLength = 0
            for user in responsePayload:
                responseLength += len(user)
            self.mutex.release()
            return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP, responseLength), responsePayload)

    def removeSpecificUserFromRoom(self, packet):
        self.mutex.acquire()
        if packet.payload.senderName in self.roomDictionary[packet.payload.roomName]:
            self.roomDictionary[packet.payload.roomName].remove(
                packet.payload.senderName)
        self.mutex.release()

    def handlePacket(self, packet: ircPacket, connection):
        # print(f"\npacket type: {type(packet)}\n")

        # register new client
        if(packet.header.opCode == ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ):
            return ircPacket(ircHeader(self.registerClient(packet.payload, connection), 0), "")

        # list rooms request
        elif (packet.header.opCode == ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ):
            rooms = list(self.roomDictionary.keys())
            temp = ircPacket(
                ircHeader(ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP, len(rooms)), rooms)
            print(f"The get all rooms response is: {type(temp)}")
            return(temp)
            # in payload

        # list users request
        elif(packet.header.opCode == ircOpcodes.IRC_OPCODE_LIST_USERS_REQ):
            length = 0
            for user in self.clientDictionary.keys():
                length += len(user)
            return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_LIST_USERS_RESP, length), list(self.clientDictionary.keys()))

        # make new room request
        elif(packet.header.opCode == ircOpcodes.IRC_OPCODE_MAKE_ROOM_REQ):
            return ircPacket(ircHeader(self.makeNewRoom(packet), 0), "")

        # join room request
        elif packet.header.opCode == ircOpcodes.IRC_OPCODE_JOIN_ROOM_REQ:
            return self.addClientToRoom(packet.payload.senderName, packet.payload.roomName)

        # list members of specific room
        elif packet.header.opCode == ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_REQ:
            return self.getMembersOfSpecificRoom(packet.payload)

        # remove user from specific room
        elif packet.header.opCode == ircOpcodes.IRC_OPCODE_LEAVE_ROOM_REQ:
            self.removeSpecificUserFromRoom(packet)

        # send message to room
        elif(packet.header.opCode == ircOpcodes.IRC_OPCODE_SEND_MSG_REQ):
            print("Server received SEND_MSG_REQ")
            return self.sendMessageRequest(packet)

        elif(packet.header.opcode == ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_REQ):
            print()
            if(packet.payload in self.clientInDictionary ):
                # make new thread
                # forward private message to packet.payload
                return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_RESP, 0), "")
            else:
                return ircPacket(ircHeader(ircOpcodes.IRC_ERR_RECIPIENT_DOES_NOT_EXIST , len(packet.payload)), packet.payload)

        # quit
        elif(packet.header.opCode == ircOpcodes.IRC_OPCODE_CLIENT_QUIT_MSG):
            self.mutex.acquire()
            print("\nReceived request to disconnect a client.")
            clientInDictionary = None
            for client, value in self.clientDictionary.items():
                if value == connection:
                    clientInDictionary = client

            if clientInDictionary != None:
                print(f"Client list beofre removing {clientInDictionary} from connected clients:\n{self.clientDictionary}")
                # self.clientDictionary.pop(clientInDictionary)
                del self.clientDictionary[clientInDictionary]
                print(f"After {clientInDictionary} was removed: ")
                print(self.clientDictionary)

            roomsClientIsIn = []
            for room, members in self.roomDictionary.items():
                for member in list(members):
                    if member == client:
                        roomsClientIsIn.append(room)


            if len(roomsClientIsIn) > 0:
                for room in roomsClientIsIn:
                    self.roomDictionary[room].remove(client)
                    print(f"{client} removed from room: {room}")

            self.mutex.release()
            return None

        # broadcast message


testServer = server()
testServer.startServer()
