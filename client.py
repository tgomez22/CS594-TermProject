
import socket
import irc_protocol
import pickle

class client:
    def __init__(self, name):
        self.name = name
        # key - senderName/roomName    value - list messages
        self.messageDictionary = dict()
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #(roomName, ("from: Tristan - yadayadayada", "from: Lydia - response"))
        
        #Tristan:
        #here is the message from Tristan
        #
        #Lydia:
        # here is a message from Lydia
        # 
        #

        self.serverPort = 6667
        self.serverIP = "127.0.0.1"
        self.buffSize = 4096


    def initializeConnection(self):
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            self.clientSocket.connect((self.serverIP, self.serverPort))
        except socket.error as e:
            print(str(e))
            
        serverResponse = self.clientSocket.recv(self.buffSize)
        byteStream = pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_REQ, len(self.name)), self.name))
        self.clientSocket.send(byteStream)
            
        serverResponse = self.clientSocket.recv(self.buffSize)
        formattedServerResponse = pickle.loads(serverResponse)
        if(formattedServerResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_REGISTER_CLIENT_RESP):
            print("Successfully joined server\n")
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
       self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_REQ, 0), "")))
       serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
       if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_ROOMS_RESP):
           print("Here is a list of valid rooms: \n")
           for room in serverResponse.payload:
               print(f"Room Name: {room}\n")
       else:
           print("Sorry we have encountered an unexpected error and could not get a list of active rooms.\n")
           print("Please try again later. \n")

    def getAllUsers(self):
        self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_REQ, 0), "")))
        serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_LIST_USERS_RESP):
            print("Here are all of the active users: \n")
            for user in serverResponse.payload:
                print(f"User: {user} \n")
        else:
            print("Sorry, we are unable to get a list of users due to an unexpected error.\n")
            print("Please try again later. \n")

    def joinARoom(self):
        self.getAllRooms()
        desiredRoom = input("What room do you wish to join?: ")
        joinRoomPayload = irc_protocol.joinRoomPayload(self.name, desiredRoom)
        payloadLength = len(desiredRoom) + len(self.name)
        joinRoomHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_REQ, payloadLength)
        self.clientSocket.send(pickle.dumps(irc_protocol.ircPacket(joinRoomHeader, joinRoomPayload)))
        serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
        
        #room successfully joined //not finished yet
        if(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_OPCODE_JOIN_ROOM_RESP):
            print(f"You have successfully joined {desiredRoom}! Start chatting now!\n")

        #too many users in room
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_TOO_MANY_USERS):
            print(f"You cannot currently join {desiredRoom} because it is currently full.\n")
            print("Please try again later.\n")
        
        #room doesn't exist
        elif(serverResponse.header.opCode == irc_protocol.ircOpcodes.IRC_ERR_ROOM_DOES_NOT_EXIST):
            print(f"Sorry, but {desiredRoom} doesn't exist. \n")
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


    
    # def sendMessage(self):
    #     userDone = False
    #     while(userDone == False):
    #         userMessage = input("Message: ")
            # if(lower(userMessage) == "-quit" or  lower(userMessage) == "-q"):
            #     userDone = True
            # elif(lower(userMessage) == "-listusers" or lower(userMessage) == "-lu"):
            #     #print users in room, may have to query server
            # elif(lower(userMessage) == "-help"):
            #     self.listCommands()
            # elif(lower(userMessage) == "-makeroom"):
            #     #send request to server #def registerRoom(self, newRoom:room, requestingClient:client):
            # elif(lower(userMessage) == "-listrooms"):
            #     #send request to server 
            # elif(lower(userMessage) == "-myrooms")
            #     # send request to server
            # else:
            #     #send to server
    
   # def showAllReceivedMessages(self, roomName: str)

    def listCommands(self):
        print("Hello, here are all the available commands: \n")
        print("'-help' for when you want to see all of these commands again. \n")
        print("'-quit' for when you want to leave your current chat room. \n")
        print("'-listusers' or '-lu' for when you want to see who else is in the room you are in. \n")
        print("'-makeroom' for when you want to make a new chat room. \n")
        print("'-listrooms' or '-lr' for when you want to see all available rooms.\n")
        print("'-myrooms' or '-mr' for when you want to see the rooms you are registered in. \n")
        print("'-exit' will end the program. \n")

    def makeRoom(self):
        roomName = input("What would you like your room to be called: ")
        payloadLength = len(roomName) + len(self.name)
        makeRoomRequestPacketHeader = irc_protocol.ircHeader(irc_protocol.ircOpcodes.IRC_OPCODE_MAKE_ROOM_REQ, payloadLength)
        makeRoomRequestPacket = irc_protocol.ircPacket(makeRoomRequestPacketHeader, irc_protocol.joinRoomPayload(self.name, roomName))

        self.clientSocket.send(pickle.dumps(makeRoomRequestPacket))
        serverResponse = pickle.loads(self.clientSocket.recv(self.buffSize))
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

        #Too many rooms already exist

        #Illegal name

        #Illegal Name length

        #generic unexpected error
            
        

    


