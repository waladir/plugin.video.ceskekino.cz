# -*- coding: utf-8 -*-
import sys

import xbmcgui
import xbmcplugin

from libs.api import call_api
from libs.session import get_token

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def play_stream(id):
    stream = call_api(api = '/video/' + str(id) + '/load/', data = None, method = 'POST', token = get_token())
    url = None
    if 'encoding' in stream:
        for encoding in stream['encoding']:
            if encoding == 'hls':
                url = 'https:' + stream['encoding'][encoding]
        if url is not None:
            list_item = xbmcgui.ListItem()
            list_item.setPath(url)
            xbmcplugin.setResolvedUrl(_handle, True, list_item)
        else:
            xbmcgui.Dialog().notification('České kino', 'Video bohužel není dostupné', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        xbmcgui.Dialog().notification('České kino', 'Video bohužel není dostupné', xbmcgui.NOTIFICATION_ERROR, 5000)
