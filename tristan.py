from client import *

Tristan = client("Tristan")
Tristan.initializeConnection()
Tristan.getAllUsers()
Tristan.makeRoom()
Tristan.joinARoom()
Tristan.clientSocket.close()