from client import *

Lydia = client("Lydia")
Lydia.initializeConnection()
Lydia.getAllUsers()
Lydia.makeRoom()
Lydia.getAllRooms()
Lydia.joinARoom()
Lydia.clientSocket.close()