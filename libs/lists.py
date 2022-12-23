# -*- coding: utf-8 -*-
import sys
import os

import xbmcgui
import xbmcplugin
import xbmcaddon

import time

from libs.api import call_api
from libs.session import get_token
from libs.data import load_cache, save_cache, get_details, set_list_item
from libs.utils import get_url, get_kodi_version

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_items(data, label, page, category_id):
    cached_data = load_cache()
    count = len(data['results'])
    pages = data['num_pages']
    if int(page) == -1:
        next = None
        previous = None
    else:
        next = data['next']
        previous = data['previous']        
    if previous is not None:
        list_item = xbmcgui.ListItem(label = 'Předchozí strana (' + str(previous) + '/' + str(pages) + ')')
        url = get_url(action='list_streams', label = label, page = int(previous), category_id = category_id, type = type)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    i = 0
    downloaded = 0
    progressbar = None
    for item in data['results']:
        i += 1
        list_item = xbmcgui.ListItem(label = item['title'])
        if str(item['id']) not in cached_data:
            if downloaded > 2:
                if progressbar is None:
                    progressbar = xbmcgui.DialogProgress()
                    progressbar.create('Stahování detailních dat')
                progressbar.update(round(i/count*100), str(i) + ' z ' + str(count))
            info = get_details(item['id'])
            time.sleep(0.5)
            downloaded += 1
        else:
            info = cached_data[str(item['id'])]
        info['image'] = item['images_hover'][0]
        info['poster'] = item['image_vertical']
        cached_data.update({str(item['id']) : info})
        list_item = set_list_item(list_item, info = cached_data[str(item['id'])])
        if cached_data[str(item['id'])]['video_id'] is None or cached_data[str(item['id'])]['video_id'] == 'None':
            info = get_details(item['id'])
            cached_data[str(item['id'])]['video_id'] = info['video_id']
        if cached_data[str(item['id'])]['type'] == 'Movie':
            url = get_url(action='play_stream', id = cached_data[str(item['id'])]['video_id'])  
            list_item.setProperty('IsPlayable', 'true')   
            if item['is_favourite'] == True:
                list_item.addContextMenuItems([('Odstranit z oblíbených', 'RunPlugin(plugin://plugin.video.ceskekino.cz?action=remove_favourite&id=' + str(item['id']) + ')',)], replaceItems = True)                       
            else:                    
                list_item.addContextMenuItems([('Přidat do oblíbených', 'RunPlugin(plugin://plugin.video.ceskekino.cz?action=add_favourite&id=' + str(item['id']) + ')',)], replaceItems = True)                       
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        else:
            url = get_url(action='list_series', id = item['id'], label = label + ' / ' + item['title'])  
            if item['is_favourite'] == True:
                list_item.addContextMenuItems([('Odstranit z oblíbených', 'RunPlugin(plugin://plugin.video.ceskekino.cz?action=remove_favourite&id=' + str(item['id']) + ')',)], replaceItems = True)                       
            else:                    
                list_item.addContextMenuItems([('Přidat do oblíbených', 'RunPlugin(plugin://plugin.video.ceskekino.cz?action=add_favourite&id=' + str(item['id']) + ')',)], replaceItems = True)                       
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    if next is not None:
        list_item = xbmcgui.ListItem(label = 'Následující strana (' + str(next) + '/' + str(pages) + ')')
        url = get_url(action='list_streams', label = label, page = int(next), category_id = category_id, type = type)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    save_cache(data = cached_data)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)    

def list_streams(label, page, category_id, type):
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    addon = xbmcaddon.Addon()
    if addon.getSetting('order') == 'abecedy':
        order = ''
    elif addon.getSetting('order') == 'datumu přidání':
        order = '&o=-published_from'
    elif addon.getSetting('order') == 'sledovanosti':
        order = '&o=-viewed_count'
    elif addon.getSetting('order') == 'hodnocení':
        order = '&o=-aggregated_rating'
    elif addon.getSetting('order') == 'nejstarší':
        order = '&o=year'
    elif addon.getSetting('order') == 'nejnovější':
        order = '&o=-year'
    if category_id is not None and category_id != 'None':
        if type == 'promo':
            data = call_api(api = '/show/shows/?page=' + str(page) + order + '&promo_categories=' + str(category_id), data = None, token = get_token())
        else:
            data = call_api(api = '/show/shows/?page=' + str(page) + order + '&categories=' + str(category_id), data = None, token = get_token())
    else:
        if type == 'favourites':
            data = call_api(api = '/show/shows/?page=' + str(page) + order + '&is_favourite=1', data = None, token = get_token())
        elif type == 'recommended':
            data = call_api(api = '/show/recommended/', data = None, token = get_token())
            if 'err' not in data:
                data = {'count' : len(data), 'num_pages' : 1, 'results' : data}
        else:
            data = call_api(api = '/show/shows/?page=' + str(page) + order, data = None, token = get_token())
    if 'count' not in data or 'num_pages' not in data or 'results' not in data:
        xbmcgui.Dialog().notification('České kino', 'Chyba při získání dat', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        list_items(data, label, page, category_id)

def list_categories(label):
    xbmcplugin.setPluginCategory(_handle, label)    
    data = call_api(api = '/show/categories/', data = None)
    for item in data:
        list_item = xbmcgui.ListItem(label = item['title'])
        if get_kodi_version() >= 20:
            infotag = list_item.getVideoInfoTag()
            infotag.setPlot(item['description'])
        else:
            list_item.setInfo('video', {'plot': item['description']})
        url = get_url(action='list_streams', label = 'Kategorie / ' + item['title'], page = 1, category_id = item['id'], type = None)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

def list_series(id, label):
    cached_data = load_cache()
    if str(id) not in cached_data:
        info = get_details(int(id))
        cached_data.update({str(id) : info})
    save_cache(cached_data)
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    data = call_api(api = '/show/shows/' + str(id) + '/', data = None, token = get_token())
    for season in data['seasons']:
        episode_number = 0
        for episode in season['episodes']:
            episode_number += 1
            list_item = xbmcgui.ListItem(label = episode['title'] + ' (' + str(episode_number) + ')')
            list_item = set_list_item(list_item = list_item, info = cached_data[str(id)])
            if get_kodi_version() >= 20:
                infotag = list_item.getVideoInfoTag()
                infotag.setPlot(episode['synopsis'])
            else:
                list_item.setInfo('video', {'plot': episode['synopsis']})
                if 'images_hover' in episode and len(episode['images_hover']) > 0:
                    list_item.setArt({'thumb': episode['images_hover'][0]})
                if 'image_vertical' in episode and len(episode['image_vertical']) > 0:
                    list_item.setArt({'poster': episode['image_vertical']})
            url = get_url(action='play_stream', id = episode['video'])  
            list_item.setProperty('IsPlayable', 'true')        
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

def list_menu():
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')

    data = call_api(api = '/show/promo-categories/', data = None)
    for item in data:
        list_item = xbmcgui.ListItem(label = item['title'])
        url = get_url(action='list_streams', label = 'Kategorie / ' + item['title'], page = 1, category_id = item['id'], type = 'promo')  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Všechny')
    url = get_url(action='list_streams', label = 'Všechny', page = 1, category_id = None, type = None)  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'all.png'), 'icon' : os.path.join(icons_dir , 'all.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Kategorie')
    url = get_url(action='list_categories', label = 'Kategorie')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'categories.png'), 'icon' : os.path.join(icons_dir , 'categories.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Doporučené')
    url = get_url(action='list_streams', label = 'Doporučené', page = -1, category_id = None, type = 'recommended')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'recommended.png'), 'icon' : os.path.join(icons_dir , 'recommended.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Oblíbené')
    url = get_url(action='list_streams', label = 'Oblíbené', page = 1, category_id = None, type = 'favourites')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'favourites.png'), 'icon' : os.path.join(icons_dir , 'favourites.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Hledat')
    url = get_url(action='list_search', label = 'Hledat')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'search.png'), 'icon' : os.path.join(icons_dir , 'search.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)    
