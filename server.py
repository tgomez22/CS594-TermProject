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

        while True:
            try:
                data = connection.recv(self.buffSize)
                # print(f"\ntype of data: {type(data)}\n")
            except:
                self.mutex.acquire()
                for key, value in self.clientDictionary.items():
                    if value == connection:
                        self.clientDictionary.pop(key)
                self.mutex.release()
                print("Cannot receive data")
                break
            if not data:
                break

            clientRequestPacket = pickle.loads(data)

            responsePacket = self.handlePacket(clientRequestPacket, connection)

            # TODO check if error message should result in server force closing a connection
            # if it should force close, send message to client stating why force closing
            # then do force close
            try:
                connection.send(pickle.dumps(responsePacket))
            except:
                print("Cannot send data")
                break
        connection.close()
        print(f"Connection closed on address {address}")
        self.threadCount -= 1

    def startServer(self):
        try:
            self.serverSocket.bind((self.host, self.port))
        except socket.error as e:
            print(str(e))

        print('Waiting for a Connection...\n')
        self.serverSocket.listen(25)  # have up to 25 connections

        while True:
            client, address = self.serverSocket.accept()

            print(f'Connected to: {address[0]}: {str(address[1])}')
            self.threadCount += 1

            print(f'Thread Number: {str(self.threadCount)}')
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
        print(f"checking if {newClient} is a legal name")
        if not self.isNameLegal(newClient):
            print(f"ERROR: name contains illegal characters: {newClient}")
            return ircOpcodes.IRC_ERR_ILLEGAL_NAME

        print(f"checking if {newClient} is already taken name")
        self.mutex.acquire()
        if newClient in list(self.clientDictionary.keys()):
            print(f"ERROR: Name already taken: {newClient} ")
            self.mutex.release()
            return ircOpcodes.IRC_ERR_NAME_EXISTS
        else:
            print(f"Client being added to server with name:{newClient}")
            self.clientDictionary[newClient] = connection
            self.roomDictionary["Lobby"].append(newClient)
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
        lengthSenderName = len(packet.payload.message.senderName)
        lengthMessage = len(packet.payload.messageBody)
        payloadLength = lengthSenderName + lengthMessage
        # ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_SEND_MSG_RESP, payloadLength), packet.payload)

    def forwardMassageToClient(self, packet: ircPacket):
        lengthSenderName = len(packet.payload.message.senderName)
        receiverName = packet.payload.receiverName
        lengthMessage = len(packet.payload.messageBody)
        payloadLength = lengthSenderName + lengthMessage

        forwardHeader = ircHeader(
            ircOpcodes.IRC_OPCODE_FORWARD_MESSAGE, payloadLength)
        forwardPacket = ircPacket(forwardHeader, ircPacket.payload)
        try:
            self.mutex.acquire()
            self.clientDictionary[receiverName].send(
                pickle.dumps(forwardPacket))
            self.mutex.release()
        except socket.error as e:
            print(str(e))

    # packet should have payload with messagePayload that contains a message object

    def sendMessageRequest(self, packet: ircPacket):
        if packet.payload.receiverName not in list(self.clientDictionary.keys()):
            if packet.payload.receiverName not in (self.roomDictionary.keys()):
                return ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST
            return ircPacket(ircHeader(ircOpcodes.IRC_ERR_RECIPIENT_DOES_NOT_EXIST, 0), "")
        else:
            # TODO make new thread
            start_new_thread(self.fowardMessageToClient, (packet, ))
            messageLen = len(packet.payload.message.messageBody)
            recipientNameLength = len(packet.payload.receiverName)
            senderNameLength = len(packet.payload.message.senderName)
            packetLength = messageLen + recipientNameLength + senderNameLength
            return ircPacket(ircHeader(ircOpcodes.IRC_OPCODE_SEND_MSG_RESP, packetLength), packet.payload)

    def getMembersOfSpecificRoom(self, desiredRoom):
        self.mutex.acquire()
        if desiredRoom not in list(self.roomDictionary.keys()):
            self.mutex.release()
            return ircPacket(ircHeader(ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST), "")
        else:
            responsePayload = list(self.roomDictionary[desiredRoom].keys())
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

        # send message
        elif(ircPacket.header.opCode == ircOpcodes.IRC_OPCODE_SEND_MSG_REQ):

            return self.sendMessageRequest(packet)

        # private message

        # broadcast message


testServer = server()
testServer.startServer()
