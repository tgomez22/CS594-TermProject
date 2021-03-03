import socket
import irc_protocol
import pickle
from _thread import *
import threading


class client:
    def __init__(self, name):
        self.name = name
        # key - senderName/roomName    value - list messages
        self.messageDictionary = dict()
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.currentRoom = ""
        self.desiredRoom = ""
        self.desiredUser = ""
        self.serverPort = 6667
        self.serverIP = "127.0.0.1"
        self.buffSize = 4096
        self.wantToQuit = False
        self.mutex = threading.Lock()

    def initializeConnection(self):
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            self.clientSocket.connect((self.serverIP, self.serverPort))
        except socket.error as e:
            print(str(e))

        try:
            serverResponse = self.clientSocket.recv(self.buffSize)
        except:
            print("Sorry, we couldn't establish an initial connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        byteStream = pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(
            irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ, len(self.name)), self.name))

        try:
            self.clientSocket.send(byteStream)
        except:
            print("Your initial header didn't go through.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        try:
            serverResponse = self.clientSocket.recv(self.buffSize)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        formattedServerResponse = pickle.loads(serverResponse)
        if(formattedServerResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_RESP):
            print("Successfully joined server\n")
            
            self.currentRoom = "Lobby"
            self.messageDictionary["Lobby"] = []

            start_new_thread(self.handleIncoming, () )
            while (self.wantToQuit == False):
                self.handleInput()
            if(self.wantToQuit == True):
                self.clientSocket.close()

        else:
            print("Couldn't join\n")
            print(f"{formattedServerResponse.header.opCode}\n")

    def handleIncoming(self):
        while self.wantToQuit == False:
            serverResponse = pickle.loads(
                self.clientSocket.recv(self.buffSize))
            self.receiveMessage(serverResponse)

    def receiveMessage(self, serverResponse):

        # IRC_OPCODE_FORWARD_MESSAGE
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_FORWARD_MESSAGE):
            self.messageDictionary[serverResponse.payload.message.receiverName] = serverResponse.payload.message.messageBody

        # IRC_OPCODE_SEND_BROADCAST_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_SEND_BROADCASE_RESP):
            for room in serverResponse.payload.message.receiverName:
                self.messageDictionary[room] = serverResponse.payload.message.messageBody

        # IRC_OPCODE_START_PRIV_CHAT_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_RESP):
            print(f"You are now chatting with {self.desiredUser}")
            self.currentRoom = "private " + self.desiredUser
            self.messageDictionary[self.currentRoom] = []

        # IRC_OPCODE_SEND_PRIV_MSG_RESP
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_SEND_PRIV_CHAT_RESP):
            self.messageDictionary[serverResponse.payload.message.receiverName] = serverResponse.payload.message.messageBody

        # IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP):
            print(f"Here are the current users in {self.currentRoom}: \n")
            for users in serverResponse.payload:
                print(f"{users}\n")

        # IRC_OPCODE_MAKE_ROOM_RESP
        # room made successfully
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_RESP):
            print(f"{self.desiredRoom} was successfully created!\n")
            self.currentRoom = self.desiredRoom
            self.desiredRoom = ""

        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_FORWARD_PRIVATE_MESSAGE):
            if serverResponse.payload.message.senderName in list(self.messageDictionary.keys()):
                self.messageDictionary[serverResponse.payload.message.senderName].append(
                    serverResponse.payload.message.messageBody)
            else:
                self.messageDictionary[serverResponse.payload.message.senderName] = serverResponse.payload.message.messageBody

        # room already exists
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ROOM_ALREADY_EXISTS):
            print(
                f"{self.desiredRoom} already exists, so you have been added to it. Start chatting now\n")
            self.currentRoom = self.desiredRoom
            print(f"Welcome to {self.currentRoom}")
            self.messageDictionary[self.currentRoom] = f"Welcome to {self.currentRoom}"

        # IRC_OPCODE_SEND_MSG_RESP
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_SEND_MSG_RESP):
            self.messageDictionary[self.currentRoom].append(
                "Me: " + serverResponse.payload.messageBody)

        # IRC_OPCODE_JOIN_ROOM_RESP
        # room successfully joined
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP):
            self.messageDictionary[self.desiredRoom] = []
            self.currentRoom = self.desiredRoom
            print(
                f"You have successfully joined {self.desiredRoom}!\nStart chatting now!\n")
            self.desiredRoom = ""

        # too many users in room
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_TOO_MANY_USERS):
            print(
                f"You cannot currently join {self.desiredRoom} because it is currently full.")
            print("Please try again later.\n")
            self.desiredRoom = ""

        # room doesn't exist
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST):
            print(f"Sorry, but the room: {self.desiredRoom} doesn't exist. \n")
            print("Please make a new room or try to join a different one.\n")
            self.desiredRoom = ""

        #already in room
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_USER_ALREADY_IN_ROOM):
            print(f"Silly goose! You are already in {self.desiredRoom}.\n")
            print("Try the '-enterroom' or '-er' command.\n")
            self.desiredRoom = ""

        # IRC_OPCODE_LIST_USERS_RESP
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_RESP):
            print("Here are all of the active users:")
            for user in serverResponse.payload:
                print(f"\tUser: {user}")

        # IRC_OPCODE_LIST_ROOMS_RESP
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP):
            roomCount = 1
            print("Here is a list of valid rooms: \n")
            for room in serverResponse.payload:
                print(f"{roomCount}. Room Name: {room}\n")
                roomCount += 1
            return serverResponse.payload

    def getAllRooms(self):
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(
                irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ, 0), "")))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def getAllUsers(self):
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(
                irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_REQ, 0), "")))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def joinARoom(self):
        self.getAllRooms()
        self.desiredRoom = input("What room do you wish to join?: ")
        joinRoomPayload = irc_protocol.joinRoomPayload(
            self.name, self.desiredRoom)
        payloadLength = len(self.desiredRoom) + len(self.name)
        joinRoomHeader = irc_protocol.ircHeader(
            irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_REQ, payloadLength)

        try:
            self.clientSocket.send(pickle.dumps(
                irc_protocol.ircPacket(joinRoomHeader, joinRoomPayload)))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def enterRoom(self):
        self.desiredRoom = input("What room would you like to enter?: ")
        self.mutex.acquire()
        if self.desiredRoom in self.messageDictionary.keys():
            self.mutex.release()
            self.currentRoom = self.desiredRoom
            self.showCurrentRoomMessages()
        else:
            self.mutex.release()
            print("Sorry that room either doesn't exist or you have not joined it yet.\n")

    def enterPrivateChat(self, desiredUser):
        self.mutex.acquire()
        if desiredUser in self.messageDictionary.keys():
            self.currentRoom = desiredUser
        self.mutex.release()

    def sendBroadcastMessage(self):
        self.mutex.acquire()
        rooms = self.getAllRooms()
        self.mutex.release()
        strDesiredRooms = input(
            "Which room numbers would you like to join? Please enter as a space separated list of numbers: ")
        indexDesiredRooms = int(strDesiredRooms.split(" "))
        i = 0
        numRooms = len(indexDesiredRooms)
        while(i < numRooms):
            indexDesiredRooms[i] -= 1
            i += 1

        desiredRooms = []
        for index in indexDesiredRooms:
            desiredRooms += rooms[index]

        message = input("Please enter the message you wish to broadcast: ")
        length = len(message) + len(desiredRooms) + len(self.name)
        broadcastHeader = irc_protocol.ircHeader(
            irc_protocol.ircOpcodes.IRC_OPCODE_SEND_BROADCAST_REQ, length)
        broadcastPayload = irc_protocol.messagePayload(
            self.name, desiredRooms, message)

        try:
            self.clientSocket.send(pickle.dumps(
                irc_protocol.ircPacket(broadcastHeader, broadcastPayload)))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def handleInput(self):
        userDone = False
        while(userDone == False):
            userMessage = input("Message: ")
            if(str.lower(userMessage) == "-quit" or str.lower(userMessage) == "-q"):
                userDone = True
                self.mutex.acquire()
                self.wantToQuit = True
                self.mutex.release()
            elif(str.lower(userMessage) == "-listusers" or str.lower(userMessage) == "-lu"):
                self.mutex.acquire()
                listUsersPayload = self.currentRoom
                length = len(self.currentRoom)
                self.mutex.release()
                listUsersHeader = irc_protocol.ircHeader(
                    irc_protocol.ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_REQ, length)
                try:
                    self.clientSocket.send(pickle.dump(
                        irc_protocol.ircPacket(listUsersHeader, listUsersPayload)))
                except:
                    print("Sorry, it seems as though you have lost connection.\n")
                    print("We are ending the program. Please try reconnecting again.\n")
                    quit()
            elif(str.lower(userMessage) == "-help"):
                self.listCommands()
            elif(str.lower(userMessage) == "-makeroom"):  # -makeroom lydiaroom
                self.makeRoom()
            elif(str.lower(userMessage) == "-listrooms"):
                self.getAllRooms()
            elif(str.lower(userMessage) == "-myrooms"):
                self.mutex.acquire()
                print("Here are the rooms you currently are a part of: \n")
                for room in self.messageDictionary.keys():
                    print(f"Room Name: {room} \n")
                print(f"You are currently IN room: {self.roomName}")
                self.mutex.release()
            # enter a room you are registered to
            elif(str.lower(userMessage == "-er") or str.lower(userMessage == "-enterroom")):
                self.enterRoom()
            # send private message
            elif(str.lower(userMessage == "-pm") or str.lower(userMessage == "-privatemessage")):
                self.sendPrivateMessage()

            # leave room
            elif(str.lower(userMessage == "-leave")):
                self.leaveRoom()

            # send broadcast message
            elif(str.lower(userMessage == "-broadcast")):
                self.sendBroadcastMessage()

            # send message to room
            else:
                self.sendMessage(userMessage)

    def sendMessage(self, userMessage):
        message = userMessage
        self.mutex.acquire()
        length = len(message) + len(self.name) + len(self.currentRoom)
        self.mutex.release()
        if "private: " in self.currentRoom:
            messageHeader = irc_protocol.ircHeader(
                irc_protocol.ircOpcodes.IRC_OPCODE_SEND_PRIV_MSG_REQ)
        else:
            self.mutex.acquire
            messageHeader = irc_protocol.ircHeader(
                irc_protocol.ircOpcodes.IRC_OPCODE_SEND_MSG_REQ, length)
            messagePayload = irc_protocol.messagePayload(
                self.name, self.currentRoom, message)
            self.mutex.release()
        try:
            self.clientSocket.send(pickle.dumps(
                irc_protocol.ircPacket(messageHeader, messagePayload)))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def sendPrivateMessage(self):
        self.desiredUser = input(
            "Who would you like to private message with?: ")
        print("\n")

        # look to see if private chat thread exists
        self.mutex.acquire()
        if f"private {self.desiredUser}" in self.messageDictionary.keys():
            privateMessageRecipient = "private " + self.desiredUser
            self.enterPrivateChat(privateMessageRecipient)
            print(f"You are now chatting with {self.desiredUser}")
            self.mutex.release()
            self.showCurrentRoomMessages()

        # start new chat thread
        else:
            length = len("private: " + self.desiredUser)
            privateMessageHeader = irc_protocol.ircHeader(
                irc_protocol.ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_REQ, length)
            privateMessagePayload = irc_protocol.messagePayload(
                self.name, "private: " + self.desiredUser, "")
            try:
                self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(
                    privateMessageHeader, privateMessagePayload)))
            except:
                print("Sorry, it seems as though you have lost connection.\n")
                print("We are ending the program. Please try reconnecting again.\n")
                quit()
        self.mutex.release()

    def showCurrentRoomMessages(self):
        self.mutex.acquire()
        print(f"Room: {self.currentRoom}")
        for message in self.messageDictionary[self.currentRoom]:
            print(f"{message}\n")
        self.mutex.release()

    def leaveRoom(self):
        self.mutex.acquire()
        if(self.currentRoom == "Lobby"):
            print("Sorry, but you cannot leave the Lobby")
        else:
            length = len(self.currentRoom) + len(self.name)
            header = irc_protocol.ircHeader(
                irc_protocol.ircOpcodes.IRC_OPCODE_LEAVE_ROOM_REQ, length)
            payload = irc_protocol.roomPayload(self.name, self.currentRoom)
            try:
                self.clientSocket.send(pickle.dumps(
                    irc_protocol.ircPacket(header, payload)))
                self.messageDictionary.pop(self.currentRoom)
                self.currentRoom = "Lobby"
            except:
                print("Sorry, it seems as though you have lost connection.\n")
                print("We are ending the program. Please try reconnecting again.\n")
                quit()
        self.mutex.release()

    def listCommands(self):
        print("Hello, here are all the available commands:")
        print("'-help' for when you want to see all of these commands again.")
        print("'-quit' or '-q' for when you want to leave your current chat room. \n")
        print("'-listusers' or '-lu' for when you want to see who else is in the room you are in.")
        print("'-makeroom' for when you want to make a new chat room. \n")
        print("'-listrooms' or '-lr' for when you want to see all available rooms.\n")
        print("'-myrooms' or '-mr' for when you want to see the rooms you are registered in. \n")
        print("'-er' or '-enterroom' for when you want to enter a new room you are already in. \n")
        print("'-pm' or '-privatemessage' for when you want to send a private message to another user.\n")
        print("'-leave' if you want to leave your current room.\n")
        print("'-exit' will end the program. \n")

    def makeRoom(self):
        self.desiredRoom = input(
            "What would you like your room to be called: ")
        payloadLength = len(self.desiredRoom) + len(self.name)
        makeRoomRequestPacketHeader = irc_protocol.ircHeader(
            irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_REQ, payloadLength)
        makeRoomRequestPacket = irc_protocol.ircPacket(
            makeRoomRequestPacketHeader, irc_protocol.joinRoomPayload(self.name, self.desiredRoom))

        try:
            self.clientSocket.send(pickle.dumps(makeRoomRequestPacket))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
