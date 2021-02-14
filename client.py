import socket

class message:
    def __init__(this, senderName: string, content: string):
        this.senderName = senderName
        this.content = content

class client:
    def __init__(this, name):
        this.name = name
        this.messageDictionary = dict()

    def receiveMessage(this, roomName: string, message: string):
        if roomName in this.messageDictionary.keys():
            this.messageDictionary[roomName].append(message)
        else: 
            this.messageDictionary[roomName] = message

    def getCurrentRooms(this):
        #ask server for all active rooms
        openRooms = # server's open rooms in array of strings format
        if(len(openRooms) == 1):
            print(f"{openRooms[i]} is the only active room")
        for roomName in openRooms:
            print(f"{roomName} is active\n")
    
    def sendMessage(this):
        bool userDone = False
        while(userDone == False):
            userMessage = input("Message: ")
            if(lower(userMessage) == "-quit" or  lower(userMessage) == "-q"):
                userDone = True
            elif(lower(userMessage) == "-listusers" or lower(userMessage) == "-lu"):
                #print users in room, may have to query server
            elif(lower(userMessage) == "-help"):
                this.listCommands()
            elif(lower(userMessage) == "-makeroom"):
                #send request to server #def registerRoom(this, newRoom:room, requestingClient:client):
            elif(lower(userMessage) == "-listrooms"):
                #send request to server 
            elif(lower(userMessage) == "-myrooms")
                # send request to server
            else:
                #send to server
    
    def listCommands(this):
        print("Hello, here are all the available commands: \n")
        print("'-help' for when you want to see all of these commands again. \n")
        print("'-quit' for when you want to leave your current chat room. \n")
        print("'-listusers' or '-lu' for when you want to see who else is in the room you are in. \n")
        print("'-makeroom' for when you want to make a new chat room. \n")
        print("'-listrooms' or '-lr' for when you want to see all available rooms.\n")
        print("'-myrooms' or '-mr' for when you want to see the rooms you are registered in. \n")

    def makeRoom(this):
        bool validRoom = False
        roomName = input("What would you like your room to be called: ")
        #send roomName to server
        validRoom = #await server response
        if(validRoom == False):
            print("Sorry, the room couldn't be made with this name. \n")
            print("Please try again later with a new name. \n")
        else:
            #change state to be in new room???????
            print("Success! You're room was able to be created.\n")
            print(f"Welcome to {roomName}")
            this.messageDictionary[roomName] = f"Welcome to {roomName}"
    
        
        




