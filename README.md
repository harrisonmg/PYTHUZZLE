# Rompecabezas

An online multiplayer jigsaw puzzle.

## How to Play

* Download the all-in-one executable for your OS from the [most recent release](https://github.com/harrisonmg/rompecabezas/releases).
* Run and enjoy!

## Controls
| Key          | Action        |
|--------------|---------------|
| Left Click   | Move Piece    |
| Right Click  | Pan           |
| Scroll Wheel | Zoom          |
| Space        | Center Puzzle |

## Manual Installation
* Download and install [Python3](https://www.python.org/downloads/)
* Install dependencies with `python3 -m pip install -r requirements.txt`. Replace `python3` with `py` for Windows platforms.
* Consult the usage information below to run.

## CLI Usage
```
usage: jigsaw.py [-h] [-o IMAGE WIDTH HEIGHT] [-c SERVER_IP]
                 [-s IMAGE WIDTH HEIGHT] [-p PORT] [-d RESOLUTION] [-n] [-e]

Do a jigsaw puzzle. The port (default=7777) must be forwarded to host an online game.

    Install dependencies:

        python3 -m pip install -r requirements.txt

    Start a 3x3 offline game:

        python3 jigsaw.py -o rock.png 3 3

    Join an online game:

        python3 jigsaw.py -c 8.8.8.8

    Host an 11x11 online game:

        python3 jigsaw.py -s itachi.png 11 11

optional arguments:
  -h, --help            show this help message and exit
  -o IMAGE WIDTH HEIGHT, --offline IMAGE WIDTH HEIGHT
                        Play an offline game
  -c SERVER_IP, --connect SERVER_IP
                        Connect to an online game
  -s IMAGE WIDTH HEIGHT, --server IMAGE WIDTH HEIGHT
                        Host an online game
  -p PORT, --port PORT  Port to connect to or host from
  -d RESOLUTION, --downscale RESOLUTION
                        Locally downscale the resolution of the puzzle's largest dimension. Not currently compatible with online.
  -n, --no-viewer       Don't open an accompanying image viewer
  -e, --escape-exit     Let the escape key exit the program.
  ```
