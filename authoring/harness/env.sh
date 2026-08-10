# env.sh - PATH for the harness. EDIT THIS FILE FOR YOUR MACHINE.
#
# The harness shells out to python and git, and an inherited PATH has proved
# unreliable under Windows/Git-Bash, so the paths are set explicitly here.
# Replace the entries below with your own interpreter and tool locations.
#
# Windows / Git-Bash example (adjust the Python version and your user name):
#   export PATH="$PATH:/c/Program Files/Python314:/c/Program Files/Python314/Scripts"
#   export PATH="$PATH:/c/Users/<you>/AppData/Roaming/npm"
#   export PATH="$PATH:/c/Program Files/nodejs"
#   export PATH="$PATH:/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin"
#   export PATH="$PATH:/c/Windows/System32:/c/Windows"
#
# Linux / macOS: usually nothing is needed here, but keep the file present -
# every script sources it.

# --- edit below ---
: "${PYTHON:=python}"
export PYTHON

# Uncomment and adapt on Windows:
# export PATH="$PATH:/c/Program Files/Python314:/c/Program Files/Python314/Scripts"
# export PATH="$PATH:/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin"
