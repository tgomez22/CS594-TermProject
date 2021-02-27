
import socket
import irc_protocol
import pickle

class client:
    def __init__(self, name):
        self.name = name
        # key - senderName/roomName    value - list messages
        self.messageDictionary = dict()        
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.currentRoom = ""
        self.serverPort = 6667
        self.serverIP = "127.0.0.1"
        self.buffSize = 4096
        self.socketsList = [input, self.serverSocket]

    def initializeConnection(self):
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            self.serverSocket.connect((self.serverIP, self.serverPort))
        except socket.error as e:
            print(str(e))
            
        try:
            serverResponse = self.serverSocket.recv(self.buffSize)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        byteStream = pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ, len(self.name)), self.name))

        try:
            self.serverSocket.send(byteStream)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
            
        try:
            serverResponse = self.serverSocket.recv(self.buffSize)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        formattedServerResponse = pickle.loads(serverResponse)
        if(formattedServerResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_RESP):
            print("Successfully joined server\n")
            self.currentRoom = "Lobby"
            self.messageDictionary["Lobby"] = []
            
        else:
            print("Couldn't join\n")
            print(f"{formattedServerResponse.header.opCode}\n")
        

        #self.clientSocket.close()

        # if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_NAME_EXISTS):
        #     print("Sorry, that name already exists. Please choose another one. \n")
        #     return False
        # elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ILLEGAL_NAME):
        #     print("Sorry, that name isn't valid. Please choose another one. \n")
        #     return False
        # else:
        #     return True
    

    def receiveMessage(self, roomName: str, receivedMessage):
        if roomName in self.messageDictionary.keys():
            self.messageDictionary[roomName].append(receivedMessage)
        else: 
            self.messageDictionary[roomName] = receivedMessage

    def getAllRooms(self):
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ, 0), "")))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        try:
            serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        roomCount = 0
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP):
            roomCount += 1
            print("Here is a list of valid rooms: \n")
            for room in serverResponse.payload:
                print(f"{roomCount}. Room Name: {room}\n")
                roomCount += 1
            return serverResponse.payload
        else:
            print("Sorry we have encountered an unexpected error and could not get a list of active rooms.\n")
            print("Please try again later. \n")

    def getAllUsers(self):
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_REQ, 0), "")))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        try:
            serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_RESP):
            print("Here are all of the active users:")
            for user in serverResponse.payload:
                print(f"\tUser: {user}")
        else:
            print("Sorry, we are unable to get a list of users due to an unexpected error.\n")
            print("Please try again later. \n")

    def joinARoom(self):
        self.getAllRooms()
        desiredRoom = input("What room do you wish to join?: ")
        joinRoomPayload = irc_protocol.joinRoomPayload(self.name, desiredRoom)
        payloadLength = len(desiredRoom) + len(self.name)
        joinRoomHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_REQ, payloadLength)

        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(joinRoomHeader, joinRoomPayload)))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        
        try:
            serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        
        #room successfully joined //not finished yet
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP):
            self.messageDictionary[desiredRoom] = []
            self.currentRoom = desiredRoom
            print(f"You have successfully joined {desiredRoom}!\nStart chatting now!\n")

        #too many users in room
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_TOO_MANY_USERS):
            print(f"You cannot currently join {desiredRoom} because it is currently full.")
            print("Please try again later.\n")
        
        #room doesn't exist
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST):
            print(f"Sorry, but the room: {desiredRoom} doesn't exist. \n")
            print("Please make a new room or try to join a different one.\n")

        #already in room
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_USER_ALREADY_IN_ROOM):
            print(f"Silly goose! You are already in {desiredRoom}.\n")
            print("Try the '-enterroom' or '-er' command.\n")

        #unexpected error code
        else:
            print("{Insert Scary Warning Message Here} ... just kidding\n")
            print("We somehow received an error that we didn't expect!\n")
            print("Please try again later.\n")

    def enterRoom(self):
        desiredRoom = input("What room would you like to enter?: ")
        if desiredRoom in self.messageDictionary.keys():
            self.currentRoom = desiredRoom
            self.showCurrentRoomMessages()
        else:
            print("Sorry that room either doesn't exist or you have not joined it yet.\n")

    def enterPrivateChat(self, desiredUser):
        if desiredUser in self.messageDictionary.keys():
            self.currentRoom = desiredUser
    
    def sendBroadcastMessage(self):
        rooms = self.getAllRooms()
        strDesiredRooms = input("Which room numbers would you like to join? Please enter as a space separated list of numbers: ")
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
        broadcastHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_SEND_BROADCAST_REQ, length)
        broadcastPayload = irc_protocol.messagePayload(self.name, desiredRooms, message)
        
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(broadcastHeader, broadcastPayload)))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

        try:
            serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()


        

    def handleInput(self):
        userDone = False
        while(userDone == False):
            userMessage = input("Message: ")
            if(str.lower(userMessage) == "-quit" or  str.lower(userMessage) == "-q"):
                userDone = True
            elif(str.lower(userMessage) == "-listusers" or str.lower(userMessage) == "-lu"):
                listUsersPayload = self.currentRoom
                length = len(self.currentRoom)
                listUsersHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_REQ, length)
                try:
                    self.clientSocket.send(pickle.dump(irc_protocol.ircPacket(listUsersHeader, listUsersPayload)))
                except:
                    print("Sorry, it seems as though you have lost connection.\n")
                    print("We are ending the program. Please try reconnecting again.\n")
                    quit()
                
                try:
                    serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
                except:
                    print("Sorry, it seems as though you have lost connection.\n")
                    print("We are ending the program. Please try reconnecting again.\n")
                    quit()

                if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP):
                    print(f"Here are the current users in {self.currentRoom}: \n")
                    for users in serverResponse.payload:
                        print(f"{users}\n")
                else:
                    print(f"We were unable to get the users of the room because it does not exist anymore. \n")

            elif(str.lower(userMessage) == "-help"):
                self.listCommands()
            elif(str.lower(userMessage) == "-makeroom"): # -makeroom lydiaroom
                self.makeRoom()
            elif(str.lower(userMessage) == "-listrooms"):
                self.getAllRooms()
            elif(str.lower(userMessage) == "-myrooms"):
                print("Here are the rooms you currently are a part of: \n")
                for room in self.messageDictionary.keys():
                    print(f"Room Name: {room} \n")
                print(f"You are currently IN room: {self.roomName}")
            #enter a room you are registered to
            elif(str.lower(userMessage == "-er") or str.lower(userMessage == "-enterroom")):
                self.enterRoom()
            #send private message
            elif(str.lower(userMessage == "-pm") or str.lower(userMessage == "-privatemessage")):
                self.sendPrivateMessage()

            #leave program
            elif(str.lower(userMessage == "-leave")):
                self.leaveRoom()

            #send broadcast message
            elif(str.lower(userMessage == "-broadcast")):
                self.sendBroadcastMessage()
            
            #send message to room
            else:
                self.sendMessage(userMessage)
                

    def sendMessage(self, userMessage):
        message = userMessage
        length = len(message) + len(self.name) + len(self.currentRoom)
        messageHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_SEND_MSG_REQ, length)
        messagePayload = irc_protocol.messagePayload(self.name, self.currentRoom, message)
        try:
            self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(messageHeader, messagePayload)))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        try:
            serverResponse = self.clientSocket.recv(self.buffSize)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        

    def sendPrivateMessage(self):
        desiredUser = input("Who would you like to private message with?: ")
        print("\n")

        #look to see if private chat thread exists
        if f"private {desiredUser}" in self.messageDictionary.keys():
            privateMessageRecipient = "private " + desiredUser
            self.enterPrivateChat(privateMessageRecipient)
            print(f"You are now chatting with {desiredUser}")
            self.showCurrentRoomMessages()

        #start new chat thread
        else:
            length = len(desiredUser)
            privateMessageHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_REQ, length)
            privateMessagePayload = irc_protocol.messagePayload(self.name, desiredUser, "")
            try:
                self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(privateMessageHeader, privateMessagePayload)))
            except:
                print("Sorry, it seems as though you have lost connection.\n")
                print("We are ending the program. Please try reconnecting again.\n")
                quit()

            try:
                serverResponse = pickle.loads(self.clientSocket.revc(self.buffSize))
            except:
                print("Unexpected server error. We apologize, but we must end the program")
                quit()
            
            if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_START_PRIV_CHAT_RESP):
                print(f"You are now chatting with {desiredUser}")
                self.currentRoom = "private " + desiredUser
                self.messageDictionary[self.currentRoom] = []

    def showCurrentRoomMessages(self):
        print(f"Room: {self.currentRoom}")
        for message in self.messageDictionary[self.currentRoom]:
            print(f"{message}\n")

    def leaveRoom(self):
        if(self.currentRoom == "Lobby"):
            print("Sorry, but you cannot leave the Lobby")
        else:
            length = len(self.currentRoom) + len(self.name)
            header = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LEAVE_ROOM_REQ, length)
            payload = irc_protocol.roomPayload(self.name, self.currentRoom)
            try:
                self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(header, payload)))
                self.messageDictionary.pop(self.currentRoom)
                self.currentRoom = "Lobby"
            except:
                print("Sorry, it seems as though you have lost connection.\n")
                print("We are ending the program. Please try reconnecting again.\n")
                quit()
            

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
        roomName = input("What would you like your room to be called: ")
        payloadLength = len(roomName) + len(self.name)
        makeRoomRequestPacketHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_REQ, payloadLength)
        makeRoomRequestPacket = irc_protocol.ircPacket(makeRoomRequestPacketHeader, irc_protocol.joinRoomPayload(self.name, roomName))

        try:
            self.clientSocket.send(pickle.dumps(makeRoomRequestPacket))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        try:
            serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()
        #print(serverResponse.decode('utf-8') + "\n")
        print(f"\ntype of server response: {type(serverResponse)}\n")

        #room made successfully
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_RESP):
            print(f"{roomName} was successfully created!\n")
            print("Enter the room to begin chatting!\n")

        #room already exists
        else:
            #change state to be in new room???????
            print("Success! You're room was able to be created.\n")
            print(f"Welcome to {roomName}")
            self.messageDictionary[roomName] = f"Welcome to {roomName}"
            self.currentRoom = roomName

        #Too many rooms already exist

        #Illegal name

        #Illegal Name length

        #generic unexpected error
            
        

    


