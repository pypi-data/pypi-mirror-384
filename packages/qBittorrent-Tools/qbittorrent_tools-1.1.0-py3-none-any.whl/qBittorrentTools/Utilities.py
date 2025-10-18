import configparser


def load_config(configuration_file_path='config.ini'):
    configuration = configparser.ConfigParser()

    # Set default values
    configuration['credentials'] = \
        {'username': '',
         'password': '',
         'server url': ''}

    configuration['path maps'] = {}

    configuration['paths'] = {
        'paths to ignore': '',
        'qbittorrent base directory': ''
    }

    configuration['trackers'] = {
        'old url prefix': '',
        'new url prefix': ''
    }

    configuration.read(configuration_file_path)

    url = configuration.get('credentials', 'server url')

    if not url.startswith('http://') and not url.startswith('https:'):
        url = 'https://' + url

    configuration.set('credentials', 'url', url)

    return configuration

def path_in_list_parents(path, path_list):
    for list_path in path_list:
        if list_path in path.parents:
            return True

    return False
