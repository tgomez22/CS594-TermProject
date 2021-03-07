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
    """Contains all of the opcodes (constant integers) to determin what action is taken on an ircPacket."""
    CLIENT_KEEPALIVE = 1001 #NOTE NOT USED
    SERVER_KEEPALIVE = 2001 #NOTE NOT USED
    ERR_ILLEGAL_LENGTH = 3002 #NOTE NOT USED
    ERR_ILLEGAL_OPCODE = 3003 #NOTE NOT USED
    ERR_ILLEGAL_MESSAGE = 3005 #NOTE NOT USED
    ERR_TOO_MANY_ROOMS = 3007 #NOTE NOT USED
    ERR_TIMEOUT = 3009 #NOTE NOT USED

    REGISTER_CLIENT_REQ = 1000
    """Sent from Client to Server, opcode to request connection."""
    LIST_ROOMS_REQ = 1002
    """Sent from client to server, request to list all rooms in server."""
    LIST_USERS_REQ = 1003
    """Sent from client to server, request to list all users joined to server."""
    JOIN_ROOM_REQ = 1004
    """Sent from client to server, request to join specified room(s) on server."""
    SEND_MSG_REQ = 1005
    """Sent from client to server, request to send a message to a room on server."""
    LIST_MEMBERS_OF_ROOM_REQ = 1006
    """Sent from client to server, request to list all users joined in a room in the server."""
    MAKE_ROOM_REQ = 1007
    """Sent from client to server, request to create a new room on the server."""
    SEND_PRIV_MSG_REQ = 1008
    """Sent from client to server, request to send a message to a user on the server."""
    START_PRIV_CHAT_REQ = 1009
    """Sent from client to server, request to send a message to a user on the server."""
    SEND_BROADCAST_REQ = 1010
    """Sent from client to server, request to send a message to multiple rooms on the server."""
    LEAVE_ROOM_REQ = 1011
    """Sent from client to server, request to leave a room on the server."""
    CLIENT_QUIT_MSG = 1012
    """Sent from client to server, request close the connection on the server."""
    
    REGISTER_CLIENT_RESP = 2000
    """Sent from server to client, success response to client request to connect to the server."""
    LIST_ROOMS_RESP = 2002
    """Sent from server to client, success response to client request to list all rooms in the server."""
    LIST_USERS_RESP = 2003
    """Sent from server to client, success response to client request to list all users in the server."""
    JOIN_ROOM_RESP = 2004
    """Sent from server to client, success response to client request to join a room in the server."""
    SEND_MSG_RESP = 2005
    """Sent from server to client, success response to client request to send a message to a room in the server."""
    MAKE_ROOM_RESP = 2006
    """Sent from server to client, success response to client request to create a new room on the server."""
    LIST_MEMBERS_OF_ROOM_RESP = 2007
    """Sent from server to client, success response to client request to list all users in a room on the server."""
    SEND_PRIV_MSG_RESP = 2008
    """Sent from server to client, success response to client request to send a private message to another client in the server."""
    START_PRIV_CHAT_RESP = 2009
    """Sent from server to client, success response to client request to start a private chat with client in the server."""
    SEND_BROADCAST_RESP = 2010
    """Sent from server to client, success response to client request to send a message to multiple rooms in the server."""
    FORWARD_MESSAGE = 2011
    """Sent from server to client, forwarded message to a client in a room in the server."""
    FORWARD_PRIVATE_MESSAGE = 2012
    """Sent from server to client, forwarded private message to a client from another client in the server."""

    IRC_ERR = 3000
    """Catchall generic error encounterd opcode."""
    ERR_NAME_EXISTS = 3001
    """Error thrown when a user tries to register with a name that is already taken on the server."""
    """Error code to indicate that the length is too long."""
    """Error code to indicate an unrecognized opcode was sent."""
    ERR_ILLEGAL_NAME = 3004
    """Error code to indicate illegal characters sent when trying to register a name of a room or user."""
    ERR_TOO_MANY_USERS = 3006
    """Error code to indicate that a room is full."""
    ERR_RECIPIENT_DOES_NOT_EXIST = 3008
    """Error code to indicate an that a client does not exist in the server when trying to send a packet to the client."""
    ROOM_DOES_NOT_EXIST = 3010
    """Error code to indicate an attempt was made to interact with a room that is not in the server."""
    ERR_ROOM_ALREADY_EXISTS = 3011
    """Error code to indicate a room already exists when trying to create a new room."""
    ERR_USER_ALREADY_IN_ROOM = 3012
    """Error code to indicate to a client that they are already joined to a room."""
    


        

        
