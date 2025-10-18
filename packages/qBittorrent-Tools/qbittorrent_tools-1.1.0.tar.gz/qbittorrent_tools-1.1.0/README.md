# qBittorrent-Tools
This project is a collection of scripts for managing torrents in a 
qBittorrent instance.

## Available Scripts
 - orphaned_torrents
 - unregistered_torrents

## Note
qBittorrent-Tools is not affiliated with the official 
[qBittorrent project.](https://www.qbittorrent.org//)

# License
This project is licensed under the MIT license. See LICENSE.txt for more 
information.

# Configuration
Create a `config.ini` file like so:

```ini
[credentials]
username = username
password = password
server url = example.com:port

[paths]
qbittorrent base directory = base torrent file path
paths to ignore = comma separated list of paths to ignore

[path maps]
path to map = value to map to

[trackers]
old url prefix = http:example.com
new url prefix = https:example.com
```

Path mapping is used to address the fact that in a docker container, the 
path seen by the qBittorrent client probably isn't the real path. For 
example, if in the container, the files are stored in `/data` but are 
physically on a RAID array, `/mnt/md0` then the following mapping would be 
needed: `/data = /mnt/md0`.

# Example Usage
Call the script function for the operation you wish to execute. The 
`config.ini` file needs to be in the same directory as your script. 

For example, if checking for unregistered torrents, the following script 
calls the appropriate function.

```python
from qBittorrentTools import Scripts


def main():
    Scripts.unregistered_torrents()
    

if __name__ == "__main__":
    main()

```
