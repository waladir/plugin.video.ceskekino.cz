# -*- coding: utf-8 -*-
import sys

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmcvfs import translatePath

import codecs

from libs.lists import list_items
from libs.api import call_api
from libs.utils import get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_search(label):
    list_item = xbmcgui.ListItem(label='Nové hledání')
    url = get_url(action='list_search_results', query = '-----', label = label + ' / ' + 'Nové hledání')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    history = load_search_history()
    for item in history:
        list_item = xbmcgui.ListItem(label=item)
        url = get_url(action='list_search_results', query = item, label = label + ' / ' + item)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle,cacheToDisc = False)

def list_search_results(query, label):
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    if query == '-----':
        input = xbmc.Keyboard('', 'Hledat')
        input.doModal()
        if not input.isConfirmed(): 
            return
        query = input.getText()
        if len(query) == 0:
            xbmcgui.Dialog().notification('České kino', 'Je potřeba zadat vyhledávaný řetězec', xbmcgui.NOTIFICATION_ERROR, 5000)
            return   
    save_search_history(query)
    data = call_api(api = '/show/search/?query=' + query, data = None)
    if 'shows' in data and len(data['shows']) > 0:
        data = {'count' : len(data['shows']), 'num_pages' : 1, 'results' : data['shows']}
        list_items(data = data, label = label, page = -1, category_id = None)
    else:
        xbmcgui.Dialog().notification('České kino','Nic nenalezeno', xbmcgui.NOTIFICATION_INFO, 3000)        

def save_search_history(query):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    max_history = 10
    cnt = 0
    history = []
    filename = addon_userdata_dir + 'search_history.txt'
    try:
        with codecs.open(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                if item != query:
                    history.append(item)
    except IOError:
        history = []
    history.insert(0,query)
    with codecs.open(filename, 'w') as file:
        for item  in history:
            cnt = cnt + 1
            if cnt <= max_history:
                file.write('%s\n' % item)

def load_search_history():
    history = []
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    filename = addon_userdata_dir + 'search_history.txt'
    try:
        with codecs.open(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                history.append(item)
    except IOError:
        history = []
    return history