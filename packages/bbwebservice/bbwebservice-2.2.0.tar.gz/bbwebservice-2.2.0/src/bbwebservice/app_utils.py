from . import url_utils

def urlencoded_to_dict(args)-> dict:

    '''Parses urlencoded payload of a POST request and sends it back as a dictionary'''
    
    assert 'post' in args, 'Either the given server-handler did not receive a POST or the wrong args were provided.'
    assert 'flags' in args, 'It seems like the wrong args were provided.'
    assert 'urlencoded' in args['flags'], 'Either the given server-handler did not receive an urlencoded POST or the wrong args were provided.'

    result = {}
    payload = args['post'].decode('utf-8')
    key_value = payload.split('&')
    for pair in key_value:
        p = pair.split('=')
        if len(p) == 2:
            result[url_utils.unescape_url(p[0])] = url_utils.unescape_url(p[1]).replace('+',' ')
    return result