from client import *
isValid = True

print("Hello, welcome to Lydia and Tristan's Irc Chat!")
name = input("Please enter your username: ")
user = client(name)
isValid = user.initializeConnection()

while(isValid == False):
    name = input("Please enter your username: ")
    user = client(name)
    isValid = user.initializeConnection()

