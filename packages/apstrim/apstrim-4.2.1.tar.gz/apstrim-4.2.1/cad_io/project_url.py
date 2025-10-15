def project_url(browser=''):
    """Return url of the gitlab project of the hosting module.
    If browser is prodided, then launch it."""
    try:    file = open('.git/config','r')
    except: return ''
    for line in file.readlines():
        try:
            suffixed = line.split('url = git@')[1]
            try:
                url = 'https://'+suffixed.rstrip('.git\n').replace(':','/')
                if not browser == '':
                    from os import system
                    system(f'{browser} {url}')
            except Exception as e:
                print(f'project_url EXCEPTION: {e}')
            return url
        except:
            continue
    return ''

