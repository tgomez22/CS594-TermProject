"""
This module contains the data structures to be used by client and server 
when transmitting and/or receiving packets.
"""
from enum import Enum


class message:
    """Contents of a message sent from one client and received by another"""
    
    def __init__( self, senderName:str, messageBody:str):
        """Create a message."""
        self.senderName = senderName
        self.messageBody = messageBody
    
        

#client to server
class messagePayload:
    """A specific payload to be passed in with an ircPacket used when
    exchanging messages.
    """
    def __init__(self, senderName: str, receiverName, messageBody:str):
        """Make a messagePayload"""
        self.receiverName = receiverName
        self.message = message(senderName, messageBody)
        

class roomPayload:
    """
    A specific payload for creating and joining rooms.
    """
    def __init__(self, senderName: str, roomName: str):
        """Create a roomPayload"""
        self.senderName = senderName
        self.roomName = roomName

class ircHeader:
    """Header information to be used by """
    def __init__(self, opCode: int, payloadLength: int):
        self.opCode = opCode
        self.payloadLength = payloadLength

class ircPacket:
    """ircPackets contain encapsulated data to be consumed by client and server."""
    def __init__(self, header: ircHeader, payload):
        self.header = header
        # self.opcode
        # self.payloadLength
        self.payload = payload


class ircOpcodes(Enum):
    """Contains all of the opcodes to determin what action is taken on an ircPacket."""
    REGISTER_CLIENT_REQ = 1000
    CLIENT_KEEPALIVE = 1001 #NOTE NOT USED
    LIST_ROOMS_REQ = 1002
    LIST_USERS_REQ = 1003
    JOIN_ROOM_REQ = 1004
    SEND_MSG_REQ = 1005
    LIST_MEMBERS_OF_ROOM_REQ = 1006
    MAKE_ROOM_REQ = 1007
    SEND_PRIV_MSG_REQ = 1008
    START_PRIV_CHAT_REQ = 1009
    SEND_BROADCAST_REQ = 1010
    IRC_OPCODE_LEAVE_ROOM_REQ = 1011
    IRC_OPCODE_CLIENT_QUIT_MSG = 1012
    
    IRC_OPCODE_REGISTER_CLIENT_RESP = 2000
    IRC_OPCODE_SERVER_KEEPALIVE = 2001
    IRC_OPCODE_LIST_ROOMS_RESP = 2002
    IRC_OPCODE_LIST_USERS_RESP = 2003
    IRC_OPCODE_JOIN_ROOM_RESP = 2004
    IRC_OPCODE_SEND_MSG_RESP = 2005
    IRC_OPCODE_MAKE_ROOM_RESP = 2006
    IRC_OPCODE_LIST_MEMBERS_OF_ROOM_RESP = 2007
    IRC_OPCODE_SEND_PRIV_MSG_RESP = 2008
    IRC_OPCODE_START_PRIV_CHAT_RESP = 2009
    IRC_OPCODE_SEND_BROADCAST_RESP = 2010
    IRC_OPCODE_FORWARD_MESSAGE = 2011
    IRC_OPCODE_FORWARD_PRIVATE_MESSAGE = 2012

    IRC_ERR = 3000
    IRC_ERR_NAME_EXISTS = 3001
    IRC_ERR_ILLEGAL_LENGTH = 3002
    IRC_ERR_ILLEGAL_OPCODE = 3003
    IRC_ERR_ILLEGAL_NAME = 3004
    IRC_ERR_ILLEGAL_MESSAGE = 3005
    IRC_ERR_TOO_MANY_USERS = 3006
    IRC_ERR_TOO_MANY_ROOMS = 3007
    IRC_ERR_RECIPIENT_DOES_NOT_EXIST = 3008
    IRC_ERR_TIMEOUT = 3009
    IRC_ERR_ROOM_DOES_NOT_EXIST = 3010
    IRC_ERR_ROOM_ALREADY_EXISTS = 3011
    IRC_ERR_USER_ALREADY_IN_ROOM = 3012
    


        

        
