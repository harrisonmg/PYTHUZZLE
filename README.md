# Rompecabezas

An online multiplayer jigsaw puzzle

![Screenshot 2022-06-14 000552](https://user-images.githubusercontent.com/3968357/173491277-0297a25a-2b27-4010-bd5c-1f948ebd941a.png)

![image](https://user-images.githubusercontent.com/3968357/173491262-71fd53c3-9b74-4aa5-8d39-6e993b7603f1.png)
![image](https://user-images.githubusercontent.com/3968357/173491221-4dfe28d5-5771-4592-ad7d-ae0e0ebe185d.png)
![image](https://user-images.githubusercontent.com/3968357/173491202-094b530a-5ea7-498c-869a-d9176b2eeb8b.png)

## Disclaimer
Code- and organization-wise, this project is pretty sloppy. But it works well enough to enjoy with my friends, so I'm leaving as is for now.

## Features
* Automatic cutting of any size puzzle
* Automatically opens image in seperate viewer
* No install necessary

## How to Play

* Download the all-in-one executable for your OS from the [most recent release](https://github.com/harrisonmg/rompecabezas/releases)
* Either host a server, connect to someones server, or play offline
* Hosts will have to [open / forward their chosen port](https://www.reddit.com/r/HomeNetworking/comments/i7ijiz/a_guide_to_port_forwarding/)

## Controls
| Key          | Action        |
|--------------|---------------|
| Left Click   | Move Piece    |
| Right Click  | Pan           |
| Scroll Wheel | Zoom          |
| Space        | Center Puzzle |

## Manual Installation
* Download and install [Python3](https://www.python.org/downloads/)
* Install dependencies with `python3 -m pip install -r requirements.txt`. Replace `python3` with `py` for Windows platforms
* Consult the CLI usage information below to run

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
