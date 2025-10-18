import pathlib

from qbittorrentapi import Client

from qBittorrentTools import Utilities


def unregistered_torrents():
    config = Utilities.load_config()

    client = Client(host=config.get('credentials', 'server url'),
                    username=config.get('credentials', 'username'),
                    password=config.get('credentials', 'password'))
    torrent_list = client.torrents.info()
    count = 0
    down_count = 0

    for torrent in torrent_list:
        for tracker in torrent.trackers:
            # Skip disabled trackers (usually DHT, PeX, and LSD)
            if tracker.status == 0:
                continue

            if tracker.msg:
                if (tracker.msg.lower().endswith(
                        'reset by peer') or tracker.msg.lower().endswith(
                    'bad gateway') or tracker.msg.lower().endswith(
                    'timed out')):
                    down_count += 1
                else:
                    count = count + 1
                    print(torrent.name, ' ', tracker.msg)

    print('Unregistered Torrents: {:.0f}'.format(count))

    if down_count > 0:
        print('Skipped {:.0f} torrents with bad tracker requests.'.format(
            down_count))


def orphaned_torrents():
    config = Utilities.load_config()

    qbt_client = Client(host=config.get('credentials', 'server url'),
                        username=config.get('credentials', 'username'),
                        password=config.get('credentials', 'password'))

    qbittorrent_base_directory = pathlib.Path(
        config.get('paths', 'qbittorrent base directory'))

    paths_to_ignore = config.get('paths', 'paths to ignore')
    paths_to_ignore = paths_to_ignore.split(',')

    path_maps_tmp = dict(config['path maps'].items())
    path_maps = {}

    for key, value in path_maps_tmp.items():
        path_maps[pathlib.Path(key)] = pathlib.Path(value)

    for i, val in enumerate(paths_to_ignore):
        paths_to_ignore[i] = pathlib.Path(val)

    torrent_paths = set()

    for torrent in qbt_client.torrents_info():
        base_path = pathlib.Path(torrent.content_path)

        if len(torrent.files) == 1:
            base_path = base_path.parent

        for key, value in path_maps.items():
            if base_path.parts[0:2] == key.parts[0:2]:
                base_path = value / pathlib.Path(*base_path.parts[2:])

        for file in torrent.files:
            path = pathlib.Path(file.name)

            if len(path.parts) > 1:
                path = pathlib.Path(*path.parts[1:])

            torrent_paths.add(base_path / path)

    print('Found {} torrent paths.'.format(len(torrent_paths)))

    file_paths = set()

    for path in qbittorrent_base_directory.rglob('*'):
        if Utilities.path_in_list_parents(path, paths_to_ignore):
            continue

        if path.is_file():
            file_paths.add(path)
        # Check for empty directories as we also want to track those
        elif path.is_dir() and not any(path.iterdir()):
            file_paths.add(path)

    print('Found {} file paths.'.format(len(file_paths)))

    orphan_paths = file_paths.difference(torrent_paths)

    print('Found {} orphan paths.\n\n'.format(len(orphan_paths)))

    if len(torrent_paths) > len(file_paths):
        error_paths = torrent_paths.difference(file_paths)

        print('Outputting error paths.')
        with open('error.txt', 'w') as f:
            for path in sorted(list(error_paths)):
                f.write(path.as_posix() + '\n')

    with open('torrents.txt', 'w') as f:
        for path in sorted(list(torrent_paths)):
            f.write(path.as_posix() + '\n')

    with open('files.txt', 'w') as f:
        for path in sorted(list(file_paths)):
            f.write(path.as_posix() + '\n')

    with open('orphans.txt', 'w') as f:
        for path in sorted(list(orphan_paths)):
            f.write(path.as_posix() + '\n')


def update_tracker_url():
    config = Utilities.load_config()

    client = Client(host=config.get('credentials', 'server url'),
                    username=config.get('credentials', 'username'),
                    password=config.get('credentials', 'password'))
    torrent_list = client.torrents.info()
    count = 0

    # Don't hit the API if we have nothing to do
    if config.get('trackers', 'old url prefix') == '':
        return

    for torrent in torrent_list:
        for tracker in torrent.trackers:

            if tracker.url.startswith(config.get('trackers', 'old url prefix')):
                new_url = tracker.url.replace(
                    config.get('trackers', 'old url prefix'),
                    config.get('trackers', 'new url prefix'))

                torrent.update_tracker_url(orig_url=tracker.url, new_url=new_url)

                count += 1

    print('Edited the tracker for torrents: {:.0f}'.format(count))
