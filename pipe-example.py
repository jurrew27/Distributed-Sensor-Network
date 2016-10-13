import sys
import time

# Read the output of pipe-example.py
string = ""
while True:
    # Read a single character.
    char = sys.stdin.read(1)

    # If the character is a newline, we have our data!
    if char == "\n":
        break

    # Append the character to the string.
    string += char

# Print something
print "Received sensor range %s" % string

# Flush stdout to make sure other processes can read from it.
sys.stdout.flush()

# Wait a while, so EOF is not yet sent.
time.sleep(10)