#!/usr/bin/env python3
import shutil
import subprocess
import sys
import os
import time
import socket

# Config #

auto_fullscreen = True
sync_mode: str = "local"  # Available modes: local only ):
mpv_socket: str = "/tmp/mpv_socket"


# End config #


# Abort function
def abort(message: str):
    print("\n" + message)
    try:
        client.close()
    except Exception:
        pass
    try:
        process.kill()
    except Exception:
        pass
    try:
        devnull.close()
    except Exception:
        pass
    sys.exit(1)


# Init sync mode (parse args)
if sync_mode == "local":
    try:
        seek = time.time() + int(sys.argv[1])*60
        file: str = sys.argv[2]
    except Exception:
        abort("Usage: " + sys.argv[0] + " MINUTES FILENAME")

    delay = seek % 60
    start_time = seek - delay + 60
else:
    abort(sync_mode + " is not a valid sync mode")

# Check file exists
if not os.path.isfile(file):
    abort(file + " is not a valid file")

# Check mpv
mpv = shutil.which("mpv")
if mpv is None:
    abort("Missing dependency: mpv")

# Start mpv
devnull = open(os.devnull, 'wb')
process = subprocess.Popen([mpv, "--input-unix-socket=" + mpv_socket, file], stdout=devnull, stderr=devnull)

# Connect to socket
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
connected = False
timeout = time.time() + 1
while not connected:
    try:
        client.connect(mpv_socket)
        connected = True
    except Exception:
        if time.time() > timeout:
            abort("Cannot connect to mpv socket")
client.send(b'{ "command": ["set_property", "pause", true] }\n')

# Start count down
now = time.time()
countdown = start_time - now

try:
    while countdown > 1:
        if process.poll() is not None:
            abort("\rStopping countdown: mpv has terminated")
        if countdown > 120:
            print("\rStarting in " + str(int(countdown/60)) + " minutes", end="")
        elif countdown > 60:
            print("\rStarting in " + str(int(countdown/60)) + " minute", end="")
        elif countdown > 10:
            print("\rStarting in " + str(int(countdown)) + " seconds", end="")
        else:
            print("\nStarting in " + str(int(countdown)), end="")
        time.sleep(1)
        countdown = start_time - time.time()
except KeyboardInterrupt:
    abort("")

print("\nEnjoy! :3")

# Start
client.send(b'{ "command": ["set_property", "pause", false] }\n')
if auto_fullscreen:
    time.sleep(0.5)
    client.send(b'{ "command": ["set_property", "fullscreen", true] }\n')

# End
client.close()
try:
    process.communicate()
except KeyboardInterrupt:
    process.kill()
devnull.close()
