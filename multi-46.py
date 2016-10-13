## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:

import subprocess

def main(nodes, r, steps):

    # Store processes.
    processes = []

    for node in range(nodes):
        
        # Open a process.
        p = subprocess.Popen(['python', 'pipe-example.py'],
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        processes.append(node)

        # Send our sensor range.
        p.stdin.write("%s\n" % r)
        p.stdin.flush()

        # Read the output of pipe-example.py
        string = ""
        while True:
            # Read a single character.
            char = p.stdout.read(1)

            # If the character is a newline, we have our data!
            if char == "\n":
                break

            # Append the character to the string.
            string += char

        print "Received something from node %d: %s" % (node, string)

if __name__ == '__main__':
    import sys, argparse
    p = argparse.ArgumentParser()
    p.add_argument('--nodes', help='number of nodes to spawn', required=True, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--steps', help='output graph info every step', action="store_true")
    args = p.parse_args(sys.argv[1:])
    main(args.nodes, args.range, args.steps)