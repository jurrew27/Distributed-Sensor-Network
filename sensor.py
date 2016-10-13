## Netwerken en Systeembeveiliging
## Lab 5 - Distributed Sensor Network
## Definitions and message format
import struct

## These are the message types.
MSG_PING       = 0 # Multicast ping.
MSG_PONG       = 1 # Unicast pong.
MSG_ECHO       = 2 # Unicast echo.
MSG_ECHO_REPLY = 3 # Unicast echo reply.

## These are the echo operations.
OP_NOOP = 0        # Do nothing.
OP_SIZE = 1        # Compute the size of network.
OP_SUM  = 2        # Compute the sum of all sensor values.
OP_MIN  = 3        # Compute the lowest sensor value.
OP_MAX  = 4        # Compute the highest sensor value.
OP_SAME = 5	       # Compute the number of sensors with the same value.

## This is used to pack message fields into a binary format.
message_format = struct.Struct('!8if')

## Length of a message in bytes.
message_length = message_format.size



def message_encode(type, sequence, initiator, neighbor, operation=0, capability=0, payload=0):
	"""
	Encodes message fields into a binary format.
	type: The message type.
	sequence: The wave sequence number.
	initiator: An (x, y) tuple that contains the initiator's position.
	neighbor: An (x, y) tuple that contains the neighbor's position.
	operation: The echo operation.
	capability: The capability range of initiator
	payload: Echo operation data (a number).
	Returns: A binary string in which all parameters are packed.
	"""
	ix, iy = initiator
	nx, ny = neighbor
	return message_format.pack(type, sequence,
		ix, iy, nx, ny, operation, capability, payload)



def message_decode(buffer):
	"""
	Decodes a binary message string to Python objects.
	buffer: The binary string to decode.
	Returns: A tuple containing all the unpacked message fields.
	"""
	type, sequence, ix, iy, nx, ny, operation, capability, payload = \
		message_format.unpack(buffer)
	return (type, sequence, (ix, iy), (nx, ny), operation, capability, payload)
