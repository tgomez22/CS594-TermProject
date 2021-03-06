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
            exit()

        byteStream = pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(
            irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ, len(self.name)), self.name))

        try:
            self.clientSocket.send(byteStream)
        except:
            print("Your initial header didn't go through.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()

        try:
            serverResponse = self.clientSocket.recv(self.buffSize)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()

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
            try:
                serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
                self.receiveMessage(serverResponse)
            except socket.error as e:
                print(f"error encountered: {e}")
                print("Ending program")
                exit()
                
            

    def receiveMessage(self, serverResponse):
        print(f"------received from server: {serverResponse.header.opCode}")
        # IRC_OPCODE_FORWARD_MESSAGE
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_FORWARD_MESSAGE):
            self.mutex.acquire()
            self.messageDictionary[serverResponse.payload.receiverName].append(
                serverResponse.payload.message.senderName + ": " + serverResponse.payload.message.messageBody)
            self.mutex.release()

        # IRC_OPCODE_SEND_BROADCAST_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_SEND_BROADCAST_RESP):
            self.mutex.acquire()
            for room in serverResponse.payload.message.receiverName:
                self.messageDictionary[room].append(serverResponse.payload.message.messageBody)
            self.mutex.release()

        # IRC_OPCODE_START_PRIV_CHAT_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_RESP):
            self.mutex.acquire()
            print(f"You are now chatting with {self.desiredUser}")
            self.currentRoom = "private: " + self.desiredUser
            self.messageDictionary[self.currentRoom] = []
            self.desiredUser = ""
            self.mutex.release()

        # IRC_OPCODE_SEND_PRIV_MSG_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_SEND_PRIV_MSG_RESP):
            self.mutex.acquire()
            self.messageDictionary[serverResponse.payload.message.receiverName].append(serverResponse.payload.message.messageBody)
            self.mutex.release()

        # IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP):
            self.mutex.acquire()
            print(f"Here are the current users in {self.currentRoom}: \n")
            
            for users in serverResponse.payload:
                print(f"{users}\n")
            self.mutex.release()

        # IRC_OPCODE_MAKE_ROOM_RESP
        # room made successfully
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_RESP):
            self.mutex.acquire()
            print(f"{self.desiredRoom} was successfully created!\n")
            self.currentRoom = self.desiredRoom
            self.desiredRoom = ""
            self.messageDictionary[self.currentRoom] = []
            self.mutex.release()

        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_FORWARD_PRIVATE_MESSAGE):
            self.mutex.acquire()
            if serverResponse.payload.message.senderName in list(self.messageDictionary.keys()):
                self.messageDictionary[serverResponse.payload.message.senderName].append(
                    serverResponse.payload.message.messageBody)
            else:
                self.messageDictionary[serverResponse.payload.message.senderName] = serverResponse.payload.message.messageBody
            self.mutex.release()

        # room already exists
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ROOM_ALREADY_EXISTS):
            self.mutex.acquire()
            print(
                f"{self.desiredRoom} already exists, so you have been added to it. Start chatting now\n")
            self.currentRoom = self.desiredRoom
            print(f"Welcome to {self.currentRoom}")
            self.messageDictionary[self.currentRoom] = f"Welcome to {self.currentRoom}"
            self.mutex.release()

        # IRC_OPCODE_SEND_MSG_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_SEND_MSG_RESP):
            self.mutex.acquire()
            print(f"received message: {serverResponse.payload.message.messageBody}")
            self.messageDictionary[self.currentRoom].append(
                "Me: " + serverResponse.payload.message.messageBody)
            self.mutex.release()

        # IRC_OPCODE_JOIN_ROOM_RESP
        # room successfully joined
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP):
            self.mutex.acquire()
            self.messageDictionary[self.desiredRoom] = []
            self.currentRoom = self.desiredRoom
            print(
                f"You have successfully joined {self.desiredRoom}!\nStart chatting now!\n")
            self.desiredRoom = ""
            self.mutex.release()

        # too many users in room
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_TOO_MANY_USERS):
            self.mutex.acquire()
            print(
                f"You cannot currently join {self.desiredRoom} because it is currently full.")
            print("Please try again later.\n")
            self.desiredRoom = ""
            self.mutex.release()

        # room doesn't exist
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST):
            self.mutex.acquire()
            print(f"Sorry, but the room: {self.desiredRoom} doesn't exist. \n")
            print("Please make a new room or try to join a different one.\n")
            self.desiredRoom = ""
            self.mutex.release()

        #already in room
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_USER_ALREADY_IN_ROOM):
            self.mutex.acquire()
            print(f"Silly goose! You are already in {self.desiredRoom}.\n")
            print("Try the '-enterroom' or '-er' command.\n")
            self.desiredRoom = ""
            self.mutex.release()

        # IRC_OPCODE_LIST_USERS_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_RESP):
            self.mutex.acquire()
            print(f"Here are all of the {len(serverResponse.payload)} active users:")
            for user in serverResponse.payload:
                print(f"\tUser: {user}")
            self.mutex.release()

        # IRC_OPCODE_LIST_ROOMS_RESP
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP):
            self.mutex.acquire()
            rooms = serverResponse.payload
            roomCount = 1
            print(f"Here is a list of {len(rooms)} valid rooms:")
            for room in rooms:
                print(f"{roomCount}. Room Name: {room}\n")
                roomCount += 1
            self.mutex.release()
            return rooms

    def getAllRooms(self):
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(
                irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ, 0), "")))
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection.")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.")
            quit()

    def getAllUsers(self):
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(
                irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_REQ, 0), "")))
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection. In getAllUsers()")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.")
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
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection. In joinARoom()")
            print(f"Error receivced: {e}")
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
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection.")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()

    def sendServerQuit(self):
        header = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_CLIENT_QUIT_MSG , 0)
        pkt = irc_protocol.ircPacket(header, "")
        self.clientSocket.send(pickle.dumps(pkt))



    def handleInput(self):
        userDone = False
        self.listCommands()
        while(userDone == False):
            userMessage = input("Message: ")
            if(str.lower(userMessage) == "-quit" or str.lower(userMessage) == "-q"):
                userDone = True
                self.wantToQuit = True
                self.sendServerQuit()
            elif(str.lower(userMessage) == "-listusers" or str.lower(userMessage) == "-lu"):
                self.mutex.acquire()
                listUsersPayload = self.currentRoom
                length = len(self.currentRoom)
                self.mutex.release()
                listUsersHeader = irc_protocol.ircHeader(
                    irc_protocol.ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_REQ, length)
                try:
                    self.clientSocket.send(pickle.dumps(
                        irc_protocol.ircPacket(listUsersHeader, listUsersPayload)))
                except socket.error as e:
                    print("\nSorry, it seems as though you have lost connection.")
                    print(f"Error receivced: {e}")
                    print("We are ending the program. Please try reconnecting again.\n")
                    quit()
            elif(str.lower(userMessage) == "-help"):
                self.listCommands()
            elif(str.lower(userMessage) == "-makeroom"):  # -makeroom lydiaroom
                self.makeRoom()
            elif(str.lower(userMessage) == "-listrooms" or str.lower(userMessage) == "-lr"):
                self.getAllRooms()
            elif(str.lower(userMessage) == "-myrooms" or str.lower(userMessage) == "-mr"):
                self.mutex.acquire()
                print("Here are the rooms you currently are a part of: \n")
                for room in self.messageDictionary.keys():
                    print(f"Room Name: {room}")
                print(f"You are currently IN room: {self.currentRoom}")
                self.mutex.release()
            # enter a room you are registered to
            elif(str.lower(userMessage) == "-er" or str.lower(userMessage) == "-enterroom"):
                self.enterRoom()
            # send private message
            elif(str.lower(userMessage) == "-pm" or str.lower(userMessage) == "-privatemessage"):
                self.sendPrivateMessage()

            # leave room
            elif(str.lower(userMessage) == "-leave"):
                self.leaveRoom()

            # send broadcast message
            elif(str.lower(userMessage) == "-broadcast"):
                self.sendBroadcastMessage()

            # list messages
            elif(str.lower(userMessage) == "-lm" or str.lower(userMessage) == "-listmessages"):
                self.showCurrentRoomMessages()
                
            # send message to room
            else:
                self.sendMessage(userMessage)

    def sendMessage(self, userMessage):
        print(f"attempting to send message to: {self.currentRoom}")
        message = userMessage
        self.mutex.acquire()
        length = len(message) + len(self.name) + len(self.currentRoom)
        self.mutex.release()
        if "private: " in self.currentRoom:
            messageHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_SEND_PRIV_MSG_REQ)
            messagePayload = ""
        else:
            self.mutex.acquire()
            messageHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_SEND_MSG_REQ, length)
            messagePayload = irc_protocol.messagePayload(self.name, self.currentRoom, message)
            self.mutex.release()
        try:
            self.clientSocket.send(pickle.dumps(
                irc_protocol.ircPacket(messageHeader, messagePayload)))
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection.")
            print(f"error received: {e}")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def sendPrivateMessage(self):
        self.desiredUser = input(
            "Who would you like to private message with?: ")


        # look to see if private chat thread exists
        self.mutex.acquire()
        if f"private: {self.desiredUser}" in self.messageDictionary.keys():
            privateMessageRecipient = "private: " + self.desiredUser
            self.enterPrivateChat(privateMessageRecipient)
            print(f"You are now chatting with {self.desiredUser}")
            self.mutex.release()
            self.showCurrentRoomMessages()

        # start new chat thread
        else:
            length = len(self.desiredUser)
            privateMessageHeader = irc_protocol.ircHeader(
                irc_protocol.ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_REQ, length)
            privateMessagePayload = irc_protocol.messagePayload(
                self.name, self.desiredUser, "")
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
        if(len(self.messageDictionary[self.currentRoom]) > 0):
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(f"\nMessages in room: {self.currentRoom}")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for message in list(self.messageDictionary[self.currentRoom]):
                print(f"{message}\n")
        else:
            print("There are no messages in this room yet.")
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
                exit()
        self.mutex.release()

    def listCommands(self):
        print("Hello, here are all the available commands:")
        print("'-lm' or '-listmessages' for when you want to see all of the messages in the room you are currently in.")
        print("'-help' for when you want to see all of these commands again.")
        print("'-quit' or '-q' for when you want to leave your current chat room. ")
        print("'-listusers' or '-lu' for when you want to see who else is in the room you are in.")
        print("'-makeroom' for when you want to make a new chat room. ")
        print("'-listrooms' or '-lr' for when you want to see all available rooms.")
        print("'-myrooms' or '-mr' for when you want to see the rooms you are registered in. ")
        print("'-er' or '-enterroom' for when you want to enter a new room you are already in. ")
        print("'-pm' or '-privatemessage' for when you want to send a private message to another user.")
        print("'-broadcast' for when you want to send a broadcast message to several rooms.")
        print("'-leave' if you want to leave your current room.")
        print("'-exit' will end the program. \n")

    def makeRoom(self):
        self.desiredRoom = input(
            "What would you like your room to be called: ")
        payloadLength = len(self.desiredRoom) + len(self.name)
        makeRoomRequestPacketHeader = irc_protocol.ircHeader(
            irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_REQ, payloadLength)
        makeRoomRequestPacket = irc_protocol.ircPacket(
            makeRoomRequestPacketHeader, irc_protocol.roomPayload(self.name, self.desiredRoom))

        try:
            self.clientSocket.send(pickle.dumps(makeRoomRequestPacket))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()
