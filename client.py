import socket
import irc_protocol

class client:
    def __init__(self, name):
        self.name = name
        # key - senderName    value - list messages
        self.messageDictionary = dict()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverPort = 6667
        self.serverIP = #??????????#
        self.buffSize = 4096

    def receiveMessage(self, roomName: str, receivedMessage: message):
        if roomName in self.messageDictionary.keys():
            self.messageDictionary[roomName].append(receivedMessage)
        else: 
            self.messageDictionary[roomName] = receivedMessage

    def getCurrentRooms(self):
        #ask server for all active rooms
        openRooms = # server's open rooms in array of strings format
        if(len(openRooms) == 1):
            print(f"{openRooms[i]} is the only active room")
        for roomName in openRooms:
            print(f"{roomName} is active\n")
    
    def sendMessage(self):
        bool userDone = False
        while(userDone == False):
            userMessage = input("Message: ")
            if(lower(userMessage) == "-quit" or  lower(userMessage) == "-q"):
                userDone = True
            elif(lower(userMessage) == "-listusers" or lower(userMessage) == "-lu"):
                #print users in room, may have to query server
            elif(lower(userMessage) == "-help"):
                self.listCommands()
            elif(lower(userMessage) == "-makeroom"):
                #send request to server #def registerRoom(self, newRoom:room, requestingClient:client):
            elif(lower(userMessage) == "-listrooms"):
                #send request to server 
            elif(lower(userMessage) == "-myrooms")
                # send request to server
            else:
                #send to server
    
    def showAllReceivedMessages(self, roomName: str)

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
        bool validRoom = False
        roomName = input("What would you like your room to be called: ")
        #send roomName to server
        validRoom = #await server response
        if(validRoom == False):
            print("Sorry, the room couldn't be made with self name. \n")
            print("Please try again later with a new name. \n")
        else:
            #change state to be in new room???????
            print("Success! You're room was able to be created.\n")
            print(f"Welcome to {roomName}")
            self.messageDictionary[roomName] = f"Welcome to {roomName}"

    def initializeConnection(self):
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.SO_KEEPALIVE, 1)
        self.socket.connect((self.serverIP, self.serverPort))
        initMessage = message(self.name, "")
        initHeader = ircHeader(1000, 0)
        initPacket = ircPacket(initHeader, initMessage)        
        self.socket.send(initPacket)

        #packet from server
        serverResponse = self.socket.recv(bufsize)
        
    def handlePacket(self, packer: ircPacket):

        

    
    
        
        




