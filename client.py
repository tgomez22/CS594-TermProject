

# low level socket library to allow ease of use when working with TCP connections.
import socket

# contains Opcodes and packet objects for use in the program.
from irc_protocol import *

# This library allows us to turn objects into a byte stream.
import pickle

# import capability to have multiple threads, allows us to handle sending and receiving at the same time.
from _thread import *
import threading
import time

class client:
    """
    This class represents a client to our IRC service. This class provides all abstractions and
    state that are needed for a client to interact with the IRC service.
    """

    def __init__(self, name):
        """Our constructor for client. It takes a name as a string for its sole argument."""
        self.name = name

        # key - senderName/roomName    value - list messages
        self.messageDictionary = dict()

        # Our constructor for client. It takes a name as a string for its sole argument.
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.currentRoom = ""
        self.desiredRoom = ""
        self.desiredUser = ""
        self.knownRooms = []
        self.knownUsers = []
        self.currentRoomUsers = []
        self.serverPort = 6667
        self.serverIP = "192.168.1.6"
        self.buffSize = 4096
        self.wantToQuit = False
        self.mutex = threading.Lock()

    def initializeConnection(self):
        """This method attempts to connect with the IRC server. If a connection is made, then the user's name
        is sent to the server for verification. If the name is legal, then the user is allowed to connect and 
        use the IRC functionality. If the name is illegal, then the program ends with a message to the user.
        The user can then attempt to enter a new name and try to connect again. """

        # This sets the option for a keepalive pulse to the server.
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # attempt to establish an initial connection. Throws an error if no connection
        # can be made
        try:
            self.clientSocket.connect((self.serverIP, self.serverPort))
        except socket.error as e:
            print(str(e))

        # catches server acknowledgement. If there is no ack, then the program ends.
        try:
            serverResponse = self.clientSocket.recv(self.buffSize)
        except:
            print("Sorry, we couldn't establish an initial connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()

        # Client sends their chosen name to the server for verification.
        # The opcode indicates that the user is wanting to join the server.
        byteStream = pickle.dumps(ircPacket(ircHeader(
            ircOpcodes.REGISTER_CLIENT_REQ, len(self.name)), self.name))

        # attempt to send the message. Throws an error and ends the program if the message cannot be sent.
        try:
            self.clientSocket.send(byteStream)
        except:
            print("Your initial header didn't go through.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()

        # attempt to receive the server's response message for name verification.
        try:
            serverResponse = self.clientSocket.recv(self.buffSize)
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()

        formattedServerResponse = pickle.loads(serverResponse)

        # If the name is valid then do initial setup like join the client to the "Lobby" room.
        # Then start a new thread that handles ONLY receiving server messages. The "main" thread
        # handles user input and sending messages to the server.
        if(formattedServerResponse.header.opCode == ircOpcodes.REGISTER_CLIENT_RESP):
            print("Successfully joined server\n")

            self.currentRoom = "Lobby"
            self.messageDictionary["Lobby"] = []

            start_new_thread(self.handleIncoming, ())
            while (self.wantToQuit == False):
                self.handleInput()
            if(self.wantToQuit == True):
                self.clientSocket.close()
                return True
        elif(formattedServerResponse.header.opCode == ircOpcodes.ERR_ILLEGAL_NAME):
            print(
                f"Sorry, but {self.name} cannot be used because it is invalid. Please enter a new name.")
            return False
        elif(formattedServerResponse.header.opCode == ircOpcodes.ERR_ILLEGAL_NAME_LENGTH):
            print(
                f"Sorry but {self.name} is too long, please try again with a new name.")
            return False
        elif(formattedServerResponse.header.opCode == ircOpcodes.ERR_NAME_EXISTS):
            print(
                f"Sorry, but {self.name} already exists. Please enter a new name.")
            return False
        else:
            print(
                "An error has occurred. Our server may be down. Please try again later.\n")
            print(f"{formattedServerResponse.header.opCode}\n")
            return "server down"

    # def sendPacketToServer(self, packet):

    def handleIncoming(self):
        """This method is only used by the secondary, "listening" thread for a client. It receives a byte stream from the server, reconstitutes it into a packet object using the
        pickle library. Then calls self.receiveMessage to handle how the client interprets the server's message."""
        while self.wantToQuit == False:
            try:
                serverResponse = pickle.loads(
                    self.clientSocket.recv(self.buffSize))
                self.receiveMessage(serverResponse)
            except socket.error as e:
                print(f"error encountered: {e}")
                print("Ending program")
                exit()

    def receiveMessage(self, serverResponse):
        """This method is only used by the secondary, "listening" thread for the client
        It takes a packet as its sole argument. This method then checks the packet's opcode to determine
        how to handle the packet."""

        # FORWARD_MESSAGE
        # A message was received from another client who is also subscribed to a room
        # that this client is also subscribed to. This will update the stored messages for this room.
        if(serverResponse.header.opCode == ircOpcodes.FORWARD_MESSAGE):
            self.mutex.acquire()
            self.messageDictionary[serverResponse.payload.receiverName].append(
                serverResponse.payload.message.senderName + ": " + serverResponse.payload.message.messageBody)
            self.mutex.release()

        # SEND_BROADCAST_RESP
        # This method updates the sending client's message dictionary for a broadcast message
        # for each successful message sent, adding those messages to their corresponding room.
        elif(serverResponse.header.opCode == ircOpcodes.SEND_BROADCAST_RESP):
            self.mutex.acquire()
            for room in serverResponse.payload.receiverName:
                self.messageDictionary[room].append(
                    "Me: " + serverResponse.payload.message.messageBody)
            self.mutex.release()

        # START_PRIV_CHAT_RESP
        # The sending client has recieved a response that they are able to initiate
        # a private chat with the requested client. This adds a new private chat room for
        # the sending client.
        elif(serverResponse.header.opCode == ircOpcodes.START_PRIV_CHAT_RESP):
            self.mutex.acquire()
            print(f"You are now chatting with {self.desiredUser}")
            self.currentRoom = "private: " + self.desiredUser
            self.messageDictionary[self.currentRoom] = []
            self.mutex.release()

        # SEND_PRIV_MSG_RESP
        # The sending client was successfully able to send a private message to another client.
        # This updates the sender's private message chat thread with the sent message.
        elif(serverResponse.header.opCode == ircOpcodes.SEND_PRIV_MSG_RESP):
            self.mutex.acquire()
            privRoomName = "private: " + self.desiredUser
            self.messageDictionary[privRoomName].append(
                "Me: " + serverResponse.payload.message.messageBody)
            self.mutex.release()

        # LIST_MEMBERS_OF_ROOM_RESP
        # The sending client was successfully able to request a list of active clients
        # who are currently in the same room as the requesting client. The list gets
        # replaced with an updated one with every call to this method.
        elif(serverResponse.header.opCode == ircOpcodes.LIST_MEMBERS_OF_ROOM_RESP):
            self.mutex.acquire()
            self.currentRoomUsers = list(serverResponse.payload)
            self.mutex.release()

        # MAKE_ROOM_RESP
        # room made successfully and the user is added to that room
        # a new entry in the message dictionary is added for the new room.
        elif(serverResponse.header.opCode == ircOpcodes.MAKE_ROOM_RESP):
            self.mutex.acquire()
            self.currentRoom = self.desiredRoom
            self.messageDictionary[self.currentRoom] = []
            self.mutex.release()

        # A client has received a private message. If the private chat thread already exists then the message
        # is appended to the corresponding entry in the message dictionary. If the chat thread does not exist then
        # a new entry is created in the message dictionary.
        elif(serverResponse.header.opCode == ircOpcodes.FORWARD_PRIVATE_MESSAGE):
            self.mutex.acquire()
            if "private: " + serverResponse.payload.message.senderName in list(self.messageDictionary.keys()):
                self.messageDictionary["private: " + serverResponse.payload.message.senderName].append(
                    serverResponse.payload.message.senderName + ": " + serverResponse.payload.message.messageBody)
            else:
                self.messageDictionary["private: " + serverResponse.payload.message.senderName] = [
                    serverResponse.payload.message.senderName + ": " + serverResponse.payload.message.messageBody]
            self.mutex.release()

        # A client attempted to create a room that already exists.
        # The room is not recreated, and the client is told that they can join it.
        elif(serverResponse.header.opCode == ircOpcodes.ERR_ROOM_ALREADY_EXISTS):
            self.mutex.acquire()
            print(f"{self.desiredRoom} already exists, you may choose to join it.\n")
            self.mutex.release()

        # SEND_MSG_RESP
        # A client was able to successfully send a message to a room.
        # The message they sent is automatically appended to that rooms message dictionary entry.
        elif(serverResponse.header.opCode == ircOpcodes.SEND_MSG_RESP):
            self.mutex.acquire()
            self.messageDictionary[self.currentRoom].append(
                "Me: " + serverResponse.payload.message.messageBody)
            self.mutex.release()

        # JOIN_ROOM_RESP
        # Client was able to successfully join their desired room.
        # a new entry in the message dictionary is made for that room and
        # the user is told of the success
        elif(serverResponse.header.opCode == ircOpcodes.JOIN_ROOM_RESP):
            self.mutex.acquire()
            print(f"Server sent back {serverResponse.payload}")
            for room in serverResponse.payload:
                if room not in self.messageDictionary.keys():
                    self.messageDictionary[room] = []
                    print(f"You have successfully joined {room}!")
            self.mutex.release()

        # too many users in room
        # client is told that they cannot enter a room since it is full
        elif(serverResponse.header.opCode == ircOpcodes.ERR_TOO_MANY_USERS):
            self.mutex.acquire()
            print(
                f"You cannot currently join {self.desiredRoom} because it is currently full.")
            print("Please try again later.\n")
            self.mutex.release()

        # room doesn't exist
        # client requested to join a room that doesn't exist. Error message
        # is given to client
        elif(serverResponse.header.opCode == ircOpcodes.ROOM_DOES_NOT_EXIST):
            self.mutex.acquire()
            print(f"Sorry, but the room: {self.desiredRoom} doesn't exist. \n")
            print("Please make a new room or try to join a different one.\n")
            self.mutex.release()

        #already in room
        # user tried to join a chat room they are already in.
        # User is prompted to change into it.
        elif(serverResponse.header.opCode == ircOpcodes.ERR_USER_ALREADY_IN_ROOM):
            self.mutex.acquire()
            print(f"Silly goose! You are already in {self.desiredRoom}.\n")
            print("Try the '-changeroom' or '-cr' command.\n")
            self.mutex.release()

        # LIST_USERS_RESP
        # Client requested all known users which are connected to the server
        # the list of all known clients is added to requesting client's state
        elif(serverResponse.header.opCode == ircOpcodes.LIST_USERS_RESP):
            self.mutex.acquire()
            self.knownUsers = serverResponse.payload
            self.mutex.release()

        # LIST_ROOMS_RESP
        # client requested a list of all chat rooms on the server.
        # server returns the list of all chat rooms and client updates its state
        elif(serverResponse.header.opCode == ircOpcodes.LIST_ROOMS_RESP):
            self.mutex.acquire()
            self.knownRooms = serverResponse.payload
            self.mutex.release()

        # Client attempted to make a room that has an illegal character in it, or it
        # begins/ends with a space character.
        elif(serverResponse.header.opCode == ircOpcodes.ERR_ILLEGAL_NAME):
            print(
                f"Sorry but {self.desiredRoom} is not a valid name. Please try making a new room with a different name.")

        # Client attempted to make a room using a name that is longer than 32 chars or has a length of 0.
        elif(serverResponse.header.opCode == ircOpcodes.ERR_ILLEGAL_ROOM_NAME_LENGTH):
            print(
                f"Sorry but {self.desiredRoom} is too long of a name. Please try making a room with a shorter name.")

        # Client attempted to send a message longer than 140 characters.
        elif(serverResponse.header.opCode == ircOpcodes.ERR_ILLEGAL_MESSAGE_LENGTH):
            print(
                "Sorry but the message you tried to send is too long. Keep it 140 characters or less.")

        # generic unexpected error. Not recoverable.
        elif(serverResponse.header.opCOde == ircOpcodes.IRC_ERR):
            print(
                "Sorry, an unexpected error has occurred and the program is now exiting.")
            quit()

            # Nothing should be able to reach this statement. This is probably
            # a catastropic error, so exit program.
        else:
            print(
                "Sorry, an unexpected error has occurred and the program is now exiting.")
            quit()

    def getAllRooms(self):
        """This method sends a request to the server asking it for a list of all public rooms that the server is
        keeping track of."""
        try:
            self.mutex.acquire()
            self.clientSocket.send(pickle.dumps(
                ircPacket(ircHeader(ircOpcodes.LIST_ROOMS_REQ, 0), "")))
            self.mutex.release()
        except socket.error as e:
            self.mutex.release()
            print("\nSorry, it seems as though you have lost connection.")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.")
            quit()

    def getAllUsers(self):
        """This method sends a request to the server asking it for a list of all connected clients."""
        try:
            self.mutex.acquire()
            self.clientSocket.send(pickle.dumps(
                ircPacket(ircHeader(ircOpcodes.LIST_USERS_REQ, 0), "")))
            self.mutex.release()
        except socket.error as e:
            self.mutex.release()
            print(
                "\nSorry, it seems as though you have lost connection. In getAllUsers()")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.")
            quit()

    def listPublicRooms(self):
        """This method displays all public chat rooms. Doesn't show private chat "rooms"."""
        index = 1
        for room in self.knownRooms:
            print(f"{index}: {room}")
            index += 1

    def joinRoom(self):
        """ This method first displays all public chat rooms on the server.
         The user can then enter a list of numbers corresponding to certain rooms.
         Then a request is sent to the server asking it to add the user to those rooms."""

        self.listPublicRooms()
        strDesiredRooms = input("Which room numbers do you wish to join?: ")
        indexDesiredRooms = strDesiredRooms.split()
        print()
        print(indexDesiredRooms)
        desiredRooms = []
        if len(indexDesiredRooms) > 0:
            i = 0
            numRooms = len(indexDesiredRooms)
            while(i < numRooms):
                strindex = indexDesiredRooms[i]
                indexDesiredRooms[i] = int(strindex) - 1
                i += 1

            self.mutex.acquire()
            for j in indexDesiredRooms:
        
                desiredRooms.append(self.knownRooms[j])
            self.mutex.release()
                
        print(f"desired rooms: {desiredRooms}")
        joinRoomPayload = roomPayload(self.name, desiredRooms)
        payloadLength = len(desiredRooms) + len(self.name)
        joinRoomHeader = ircHeader(
            ircOpcodes.JOIN_ROOM_REQ, payloadLength)

        try:
            self.clientSocket.send(pickle.dumps(
                ircPacket(joinRoomHeader, joinRoomPayload)))
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection. In joinARoom()")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def changeRoom(self):
        """This method lets a user change state into a room that they are currently joined to.
        It will then print the messages for that room."""

        self.desiredRoom = input("What room would you like to enter?: ")
        self.mutex.acquire()

        if self.desiredRoom in self.messageDictionary.keys():
            self.currentRoom = self.desiredRoom
            self.mutex.release()
            self.showCurrentRoomMessages()
        else:
            self.mutex.release()
            print("Sorry that room either doesn't exist or you have not joined it yet.\n")

    def enterPrivateChat(self, desiredUser):
        """This method allows the user to change state into a private chat with another client"""

        self.mutex.acquire()
        if desiredUser in self.messageDictionary.keys():
            self.currentRoom = desiredUser
        self.mutex.release()

    def sendBroadcastMessage(self):
        """This method allows a client to send a broadcast message to multiple rooms they are subscribed to. """
        """The client can select the rooms to broadcast to then they can enter their message."""
        """The request is then sent to the server for verification/handling."""
        self.mutex.acquire()
        rooms = list(self.messageDictionary.keys())
        self.mutex.release()
        index = 1
        for room in rooms:
            print(f"{index}: {room}")
            index += 1
        strDesiredRooms = input(
            "Which room numbers would you like to join? Please enter as a space separated list of numbers: ")
        indexDesiredRooms = strDesiredRooms.split(" ")

        if len(indexDesiredRooms) > 1:
            i = 0
            numRooms = len(indexDesiredRooms)
            while(i < numRooms):
                strindex = indexDesiredRooms[i]
                indexDesiredRooms[i] = int(strindex) - 1
                i += 1

            desiredRooms = []
            for j in indexDesiredRooms:
                desiredRooms.append(rooms[j])

            message = input("Please enter the message you wish to broadcast: ")
            length = len(message) + len(desiredRooms) + len(self.name)
            broadcastHeader = ircHeader(ircOpcodes.SEND_BROADCAST_REQ, length)
            broadcastPayload = messagePayload(self.name, desiredRooms, message)

            try:
                self.clientSocket.send(pickle.dumps(
                    ircPacket(broadcastHeader, broadcastPayload)))
            except socket.error as e:
                print("\nSorry, it seems as though you have lost connection.")
                print(f"Error receivced: {e}")
                print("We are ending the program. Please try reconnecting again.\n")
                exit()
        else:
            print("")

    def sendServerQuit(self):
        """The method is for when the client desires to quit the chat program. It sends a request to the server to leave"""
        header = ircHeader(ircOpcodes.CLIENT_QUIT_MSG, 0)
        pkt = ircPacket(header, "")
        try:
            self.clientSocket.send(pickle.dumps(pkt))
        except socket.error as e:
            print(f"error occurred: {e}")

    def listUsers(self):
        """This method lists the current users of the room the client is currently in."""
        print(f"Here are the users in {self.currentRoom}")
        self.mutex.acquire()
        for user in self.currentRoomUsers:
            if user == self.name:
                print("Me!")
            else:
                print(user)
        self.mutex.release()

    def getUsersInCurrentRoom(self):
        """This method sends a request to the server for a list of users 
            who are in the room that the requesting client currently is in"""
        self.mutex.acquire()
        if "private: " in self.currentRoom:
            self.mutex.release()
            return
        listUsersPayload = str(self.currentRoom)
        length = len(listUsersPayload)
        listUsersHeader = ircHeader(ircOpcodes.LIST_MEMBERS_OF_ROOM_REQ, length)
        pkt = ircPacket(listUsersHeader, listUsersPayload)
        try:
            
            self.clientSocket.send(pickle.dumps(pkt))
            self.mutex.release()
        except socket.error as e:
            self.mutex.release()
            print("\nSorry, it seems as though you have lost connection.")
            print(f"Error receivced: {e}")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def listCommands(self):
        """This method displays to the client a list of available actions in the program."""
        print("Enter a message to send to your current room or enter a command.")
        print("Available commands:")
        print("------------------------------ to send a message to the current room, just type it and send")
        print("'-help'            or '-h'     to see all of these commands again.")
        print("'-privatemessage'  or '-pm'    to send a private message to another user.")
        print("'-broadcast'       or '-bm'    to send a broadcast message to several rooms.")
        print("'-listmessages'    or '-lm'    to see all of the messages in the room you are currently in.")
        print("'-joinroom'        or '-j'     to join a public chat room.")
        print("'-listusers'       or '-lu'    to see who else is in the room you are in.")
        print("'-makeroom'        or '-mkrm'  to make a new chat room. ")
        print("'-changeroom'      or '-cr'    to change to a room you are joined. ")
        print("'-listpublicrooms' or '-lpr'   to see all available rooms.")
        print("'-myrooms'         or '-myrms' to see the rooms you are registered in. ")
        print("'-leaveroom'       or '-lrm'    to unsubscribe from your current room.")
        print("'-quit'            or '-q'     to end the program. ")

    def handleInput(self):
        """This method handles user input in the program. """
        userDone = False

        # initial entry in the program lists all commands to the user.
        self.listCommands()
        while(userDone == False):

            # Upon every iteration, the state of known rooms, all known users, and all users in the
            # clients current room are updated.
            time.sleep(1)
            self.getUsersInCurrentRoom()
            time.sleep(1)
            self.getAllRooms()
            time.sleep(1)
            self.getAllUsers()

            messageBody=input("Message: ")
            userMessage = str.lower(messageBody)

            if(userMessage == "-quit" or userMessage == "-q"):
                userDone = True
                self.wantToQuit = True
                self.sendServerQuit()

            elif(userMessage == "-listusers" or userMessage == "-lu"):
                self.listUsers()

            elif(userMessage == "-help" or userMessage == "-h"):
                self.listCommands()

            elif(userMessage == "-makeroom" or userMessage == "-mkrm"):  # -makeroom lydiaroom
                self.makeRoom()

            elif(userMessage == "-listpublicrooms" or userMessage == "-lpr"):
                self.listPublicRooms()

            elif(userMessage == "-joinroom" or userMessage == '-j'):
                self.joinRoom()

            elif(userMessage == "-myrooms" or userMessage == "-myrms"):
                self.listMyRooms()

            # enter a room you are registered to
            elif(userMessage == "-cr" or userMessage == "-changeroom"):
                self.changeRoom()

            # send private message
            elif(userMessage == "-pm" or userMessage == "-privatemessage"):
                self.sendPrivateMessage()

            # leave room
            elif(userMessage == "-leaveroom" or userMessage == "-lrm"):
                self.leaveRoom()

            # send broadcast message
            elif(userMessage == "-broadcast" or userMessage == "-bm"):
                self.sendBroadcastMessage()

            # list messages
            elif(userMessage == "-lm" or userMessage == "-listmessages"):
                self.showCurrentRoomMessages()

            # send message to room
            else:
                self.sendMessage(userMessage)

    def listMyRooms(self):
        """This method displays all of the rooms a user is currently joined to. """
        self.mutex.acquire()
        print("Here are the rooms you currently are a part of: \n")
        for room in self.messageDictionary.keys():
            print(f"Room Name: {room}")
        print(f"\nYou are currently IN room: {self.currentRoom}")
        self.mutex.release()

    def sendMessage(self, userMessage):
        """This method handles the logic of sending a message to a room, or to a particular client in the 
        case of private messaging.
        """
        message = userMessage
        self.mutex.acquire()
        length = len(message) + len(self.name) + len(self.currentRoom)
        self.mutex.release()
        if "private: " in self.currentRoom:  # private: Tristan
            self.mutex.acquire()
            temp = self.currentRoom.split()
            self.desiredUser = temp[1]
            messageHeader = ircHeader(ircOpcodes.SEND_PRIV_MSG_REQ, length)
            msgPayload = messagePayload(
                self.name, self.desiredUser, message)
            self.mutex.release()
        else:
            self.mutex.acquire()
            messageHeader = ircHeader(ircOpcodes.SEND_MSG_REQ, length)
            msgPayload = messagePayload(
                self.name, self.currentRoom, message)
            self.mutex.release()
        try:
            self.clientSocket.send(pickle.dumps(
                ircPacket(messageHeader, msgPayload)))
        except socket.error as e:
            print("\nSorry, it seems as though you have lost connection.")
            print(f"error received: {e}")
            print("We are ending the program. Please try reconnecting again.\n")
            quit()

    def showKnownUsers(self):
        """This method displays all clients connected to the server."""
        print("Here is a list of every user who is currently online:")
        for user in self.knownUsers:
            if(user == self.name):
                print("Me!")
            else:
                print(user)

    def sendPrivateMessage(self):
        """This method allows a client to initiate a new private chat with a particular client
        or allows a client to continue an already existing private chat. """

        self.showKnownUsers()
        self.desiredUser = input(
            "Who would you like to private message with?: ")

        # look to see if private chat thread exists
        self.mutex.acquire()
        if f"private: {self.desiredUser}" in self.messageDictionary.keys():
            self.mutex.release()
            privateMessageRecipient = "private: " + self.desiredUser
            self.enterPrivateChat(privateMessageRecipient)
            print(f"You are now chatting with {self.desiredUser}")
            self.showCurrentRoomMessages()
        

        # start new chat thread
        else:
            length = len(self.desiredUser)
            privateMessageHeader = ircHeader(
                ircOpcodes.START_PRIV_CHAT_REQ, length)
            privateMessagePayload = messagePayload(
                self.name, self.desiredUser, "")
            self.mutex.release()
            try:
                self.clientSocket.send(pickle.dumps(
                    ircPacket(privateMessageHeader, privateMessagePayload)))
            except:
                print("Sorry, it seems as though you have lost connection.\n")
                print("We are ending the program. Please try reconnecting again.\n")
                quit()
            return 

    def showCurrentRoomMessages(self):
        """This method displays all of the stored messages in the current room the client is in."""
        self.mutex.acquire()
        if(len(self.messageDictionary[self.currentRoom]) > 0):
            print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(f"Messages in room: {self.currentRoom}")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for message in list(self.messageDictionary[self.currentRoom]):
                print(f"{message}\n")
        else:
            print("There are no messages in this room yet.")
        self.mutex.release()

    def leaveRoom(self):
        """This method allows a client to leave a room they currently are joined to."""
        self.mutex.acquire()
        if(self.currentRoom == "Lobby"):
            print("Sorry, but you cannot leave the Lobby")
        else:
            length = len(self.currentRoom) + len(self.name)
            header = ircHeader(ircOpcodes.LEAVE_ROOM_REQ, length)
            payload = roomPayload(self.name, self.currentRoom)
            try:
                self.clientSocket.send(
                    pickle.dumps(ircPacket(header, payload)))
                self.messageDictionary.pop(self.currentRoom)
                self.currentRoom = "Lobby"
            except:
                print("Sorry, it seems as though you have lost connection.\n")
                print("We are ending the program. Please try reconnecting again.\n")
                exit()
        self.mutex.release()

    def makeRoom(self):
        """This method allows a client to make a new public chat room for other users to join."""

        self.desiredRoom = input(
            "What would you like your room to be called: ")
        payloadLength = len(self.desiredRoom) + len(self.name)
        makeRoomRequestPacketHeader = ircHeader(
            ircOpcodes.MAKE_ROOM_REQ, payloadLength)
        makeRoomRequestPacket = ircPacket(
            makeRoomRequestPacketHeader, roomPayload(self.name, self.desiredRoom))

        try:
            self.clientSocket.send(pickle.dumps(makeRoomRequestPacket))
        except:
            print("Sorry, it seems as though you have lost connection.\n")
            print("We are ending the program. Please try reconnecting again.\n")
            exit()
