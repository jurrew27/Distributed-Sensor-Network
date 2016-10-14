# Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
# NAME: Matthijs de Wit, Jurre Wolsink
# STUDENT ID: 0000000, 10580476
import sys
import struct
from socket import *
from select import *
from random import randint
from gui import MainWindow
from sensor import *
from math import *


# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)


def to_dict_key(sequence, address):
    return str(sequence) + str(address[0]) + str(address[1])


class Sensor:
    def __init__(self, mcast_addr, sensor_pos, sensor_range, sensor_val,
            grid_size, ping_period):
        """
        mcast_addr: udp multicast (ip, port) tuple.
        sensor_pos: (x,y) sensor position tuple.
        sensor_range: range of the sensor ping (radius).
        sensor_val: sensor value.
        grid_size: length of the  of the grid (which is always square).
        ping_period: time in seconds between multicast pings.
        """
        self.mcast_addr = mcast_addr
        self.sensor_pos = sensor_pos
        self.sensor_range = sensor_range
        self.sensor_val = sensor_val
        self.grid_size = grid_size
        self.neighbors = []
        self.sequence_number = 0
        self.fathers = dict()
        self.received = []

        # -- Create the multicast listener socket. --
        mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Subscribe the socket to multicast messages from the given address.
        mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
        mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        if sys.platform == 'win32':  # windows special case
            mcast.bind(('localhost', mcast_addr[1]))
        else:  # should work for everything else
            mcast.bind(mcast_addr)

        # -- Create the peer-to-peer socket. --
        peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Set the socket multicast TTL so it can send multicast messages.
        peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
        # Bind the socket to a random port.
        if sys.platform == 'win32':  # windows special case
            peer.bind(('localhost', INADDR_ANY))
        else:  # should work for everything else
            peer.bind(('', INADDR_ANY))

        # -- make the gui --
        window = MainWindow()
        window.writeln('my address is %s:%s' % peer.getsockname())
        window.writeln('my position is (%s, %s)' % sensor_pos)
        window.writeln('my sensor value is %s' % sensor_val)

        self.mcast = mcast
        self.peer = peer
        self.window = window

    def main(self):
        # -- This is the event loop. --
        while self.window.update():
            rlist, _, _ = select([self.mcast, self.peer], [], [], 0)
            for recv in rlist:
                (data, addr) = recv.recvfrom(4096)
                command, sequence, initiator, neighbor, _, init_range, _ = message_decode(data)
                if command == MSG_PING:
                    self.recv_ping(initiator, init_range, addr)
                elif command == MSG_PONG:
                    self.recv_pong(neighbor, addr)
                elif command == MSG_ECHO:
                    self.recv_echo(sequence, initiator, addr)
                elif command == MSG_ECHO_REPLY:
                    self.recv_echo_reply(sequence, initiator, addr)

            command = self.window.getline()
            if command == 'ping':
                self.send_ping()
            elif command == 'list':
                self.window.writeln(self.neighbors)
            elif command == 'move':
                self.sensor_pos = random_position(self.grid_size)
                self.window.writeln('my position is (%s, %s)' % self.sensor_pos)
            elif command.startswith('set'):
                new_range = int(command.split()[1])
                if new_range % 10 == 0 and new_range >= 20 and new_range <= 70:
                    self.sensor_range = new_range
                self.window.writeln('sensor range is %s' % self.sensor_range)
            elif command == 'echo':
                self.send_echo(self.sequence_number, self.sensor_pos)
                self.sequence_number = self.sequence_number + 1

    def send_ping(self):
        self.neighbors = []
        msg = message_encode(
            MSG_PING,
            0,
            self.sensor_pos,
            self.sensor_pos,
            0,
            self.sensor_range,
            0
        )
        self.peer.sendto(msg, mcast_addr)
        self.window.writeln('pinging...')

    def recv_ping(self, initiator, init_range, addr):
        dist = sqrt(pow(abs(initiator[0] - self.sensor_pos[0]), 2) +
                pow(abs(initiator[1] - self.sensor_pos[1]), 2))
        if round(dist) == 0 or dist > init_range:
            return

        self.window.writeln('ping recieved from: (%s, %s)' % initiator)

        self.send_pong(initiator, init_range, addr)

    def send_pong(self, initiator, init_range, addr):
        msg = message_encode(
            MSG_PONG,
            0,
            initiator,
            self.sensor_pos,
            0,
            init_range,
            0
        )
        self.peer.sendto(msg, addr)
        self.window.writeln('pong send')

    def recv_pong(self, neighbor, addr):
        self.window.writeln('pong recieved from: (%s, %s)' % neighbor)
        self.neighbors.append([neighbor, addr])

    def send_echo(self, sequence, initiator):
        msg = message_encode(
            MSG_ECHO,
            sequence,
            initiator,
            self.sensor_pos,
            OP_NOOP
        )

        neighbors_to_send = self.neighbors
        if to_dict_key(sequence, initiator) in self.fathers:
            father = self.fathers[to_dict_key(sequence, initiator)]
            neighbors_to_send = filter(lambda nb: nb[1] != father, self.neighbors)

        for node in neighbors_to_send:
            self.peer.sendto(msg, node[1])
            self.window.writeln('echo send to: %s:%s' % node[1])

    def recv_echo(self, sequence, initiator, addr):
        self.window.writeln('echo recieved from: %s:%s' % addr)

        if to_dict_key(sequence, initiator) in self.fathers or len(self.neighbors) == 1:
            self.send_echo_reply(sequence, initiator, addr)
        else:
            self.fathers.update({to_dict_key(sequence, initiator): addr})
            self.send_echo(sequence, initiator)

    def send_echo_reply(self, sequence, initiator, addr):
        msg = message_encode(
            MSG_ECHO_REPLY,
            sequence,
            initiator,
            self.sensor_pos,
            OP_NOOP
        )

        self.peer.sendto(msg, addr)
        self.window.writeln('echo reply send to: %s:%s' % addr)

    def recv_echo_reply(self, sequence, initiator, addr):
        self.window.writeln('echo reply recieved from: %s:%s' % addr)

        if (sequence, initiator, addr) not in self.received:
            self.received.append((sequence, initiator, addr))

        received_neighbors = filter(lambda nb: nb[0] == sequence and nb[1] == initiator, self.received)

        if len(received_neighbors) == len(self.neighbors) and self.sensor_pos == initiator:
            self.window.writeln('decide')
        elif len(received_neighbors) + 1 >= len(self.neighbors) and self.sensor_pos != initiator:
            self.send_echo_reply(
                sequence,
                initiator,
                self.fathers[to_dict_key(sequence, initiator)]
            )


# -- program entry point --
if __name__ == '__main__':
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.1')
    p.add_argument('--port', help='multicast port', default=50000, type=int)
    p.add_argument('--pos', help='x,y sensor position', default=None)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--value', help='sensor value', default=-1, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
                   default=5, type=int)
    args = p.parse_args(sys.argv[1:])
    if args.pos:
        pos = tuple(int(n) for n in args.pos.split(',')[:2])
    else:
        pos = random_position(args.grid)
    if args.value >= 0:
        value = args.value
    else:
        value = randint(0, 100)
    mcast_addr = (args.group, args.port)
    sensor = Sensor(mcast_addr, pos, args.range, value, args.grid, args.period)
    sensor.main()
