# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from urllib.request import urlopen, Request
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.error import HTTPError

import json
import codecs
import time

from xbmcvfs import translatePath

_url = sys.argv[0]
if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

token = None

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def call_api(api, data, method = None):
    global token
    url = 'https://www.ceskekino.cz/api/v1' + api
    if token is not None:
        headers = {'X-Authorization' : 'Token ' + token, 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    else:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    if data != None:
        data = json.dumps(data).encode("utf-8")
    if method is not None:
        request = Request(url = url, data = data, method = method, headers = headers)
    else:
        request = Request(url = url, data = data, headers = headers)
    try:
        html = urlopen(request).read()
        if html and len(html) > 0:
            data = json.loads(html)
            return data
        else:
            return []
    except HTTPError as e:
        return { 'err' : e.reason }      

def get_token():
    global token
    addon = xbmcaddon.Addon()
    if not addon.getSetting('email') or len(addon.getSetting('email')) > 0 and not addon.getSetting('password') and len(addon.getSetting('password')) == 0:
        xbmcgui.Dialog().notification('České kino', 'Zadejte v nastavení přihlašovací údaje', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    data = None
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'session.txt')
    try:
        with codecs.open(filename, 'r', encoding='utf-8') as file:
            for row in file:
                data = row[:-1]
    except IOError as error:
        if error.errno != 2:
            xbmcgui.Dialog().notification('České kino', 'Chyba při načtení session', xbmcgui.NOTIFICATION_ERROR, 5000)
    if data is not None:
        data = json.loads(data)
        if 'token' in data and 'valid_to' in data and data['valid_to'] > int(time.time()):
            return data['token']
    post = {'email' : addon.getSetting('email'), 'password' : addon.getSetting('password')}
    data = call_api(api = '/account/login-user/', data = post)
    if 'token' in data:
        token = data['token']
        data = call_api(api = '/account/profiles/', data = None)
        id = -1
        if len(data) > 0:
            id = data[0]['id']
        data = call_api(api = '/account/login-profile/' + str(id) + '/', data = None, method = 'POST')
        if 'token' in data:
            token = data['token']
            data = json.dumps({'token' : token, 'valid_to' : int(time.time()) + 60*60*24})
            try:
                with codecs.open(filename, 'w', encoding='utf-8') as file:
                    file.write('%s\n' % data)
            except IOError:
                xbmcgui.Dialog().notification('České kino', 'Chyba uložení session', xbmcgui.NOTIFICATION_ERROR, 5000)
            return token
        else:
            xbmcgui.Dialog().notification('České kino', 'Chyba při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
    else:
        xbmcgui.Dialog().notification('České kino', 'Chyba při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()

def remove_session():
    global token
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'session.txt')
    if os.path.exists(filename):
        try:
            os.remove(filename) 
        except IOError:
            xbmcgui.Dialog().notification('České kino', 'Chyba při resetu session', xbmcgui.NOTIFICATION_ERROR, 5000)
    token =  get_token()
    xbmcgui.Dialog().notification('České kino', 'Byla vytvořená nová session', xbmcgui.NOTIFICATION_INFO, 5000)

def load_cache():
    data = {}
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'cached_data.txt')
    try:
        with codecs.open(filename, 'r', encoding='utf-8') as file:
            for row in file:
                data = row[:-1]
    except IOError as error:
        if error.errno != 2:
            xbmcgui.Dialog().notification('České kino', 'Chyba při načtení cache', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
        else:
            data = '{}'
    if data is not None:
        data = json.loads(data)
    return data

def save_cache(data):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'cached_data.txt')
    data = json.dumps(data)
    try:
        with codecs.open(filename, 'w', encoding='utf-8') as file:
            file.write('%s\n' % data)
    except IOError:
        xbmcgui.Dialog().notification('České kino', 'Chyba uložení cache', xbmcgui.NOTIFICATION_ERROR, 5000)

def reset_cache():
    save_cache(data = {})
    xbmcgui.Dialog().notification('České kino', 'Stažená detailní data byla smazána', xbmcgui.NOTIFICATION_INFO, 5000)

def get_details(id):
    global token
    token =  get_token()
    data = call_api(api = '/show/shows/' + str(id) + '/', data = None)
    if 'id' in data:
        if 'video' in data:
            video_id = data['video']
        else:
            video_id = -1
        if 'countries' in data and len(data['countries']) > 0:
            country = data['countries'][0]
        else:
            country = None
        image = data['image_video']
        poster = data['image_vertical']
        cast = []
        directors = []
        for actor in data['actors']:
            cast.append(actor['name'])
        for director in data['directors']:
            directors.append(director['name'])
        rating = data['aggregated_rating']
        if data['show_type'] == 'Serial':
            duration = -1
        else:
            duration = data['length']
        return {'id' : data['id'], 'video_id' : video_id, 'type' : data['show_type'], 'title' : data['title'], 'description' : data['description'], 'image' : image, 'poster' : poster, 'country' : country, 'genres' : data['genres'], 'year' : data['year'], 'cast' : cast, 'directors' : directors, 'duration' : duration, 'rating' : rating}
    else:
        return None

def set_list_item(list_item, info):
    cast = []
    directors = []
    genres = []
    list_item.setInfo('video', {'mediatype' : 'movie'})
    list_item.setInfo('video', {'plot': info['description']})
    list_item.setInfo('video', {'year': info['year']})
    list_item.setInfo('video', {'country': info['country']})
    for genre in info['genres']:      
        genres.append(genre)
    list_item.setInfo('video', {'genre' : genres})    
    if len(info['cast']) > 0:
        for person in info['cast']:      
            cast.append(person)
        list_item.setInfo('video', {'cast' : cast})  
    if len(info['directors']) > 0:
        for person in info['directors']:      
            directors.append(person)
        list_item.setInfo('video', {'director' : directors})  
    if 'duration' in info:
        list_item.setInfo('video', {'duration': info['duration']})
    list_item.setArt({'thumb': info['image']})
    list_item.setArt({'poster': info['poster']})
    if 'rating' in info:
        list_item.setRating('rating', round(float(info['rating'])/10, 1))
    return list_item

def play_stream(id):
    global token
    token =  get_token()
    stream = call_api(api = '/video/' + str(id) + '/load/', data = None, method = 'POST')
    url = None
    for encoding in stream['encoding']:
        if encoding == 'hls':
            url = 'https:' + stream['encoding'][encoding]
    if url is not None:
        list_item = xbmcgui.ListItem()
        list_item.setPath(url)
        xbmcplugin.setResolvedUrl(_handle, True, list_item)

def list_streams(label, page, id, type):
    global token
    token =  get_token()
    cached_data = load_cache()
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
    if id is not None and id != 'None':
        if type == 'promo':
            data = call_api(api = '/show/shows/?page=' + str(page) + order + '&promo_categories=' + str(id), data = None)
        else:
            data = call_api(api = '/show/shows/?page=' + str(page) + order + '&categories=' + str(id), data = None)
    else:
        if type == 'favourites':
            data = call_api(api = '/show/shows/?page=' + str(page) + order + '&is_favourite=1', data = None)
        else:
            data = call_api(api = '/show/shows/?page=' + str(page) + order, data = None)
    if 'count' not in data or 'num_pages' not in data or 'results' not in data:
        xbmcgui.Dialog().notification('České kino', 'Chyba při získání dat', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        count = len(data['results'])
        pages = data['num_pages']
        next = data['next']
        previous = data['previous']        
        if previous is not None:
            list_item = xbmcgui.ListItem(label = 'Předchozí strana (' + str(previous) + '/' + str(pages) + ')')
            url = get_url(action='list_streams', label = label, page = int(previous), id = id, type = type)  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        progressbar = None
        i = 0
        for item in data['results']:
            i += 1
            list_item = xbmcgui.ListItem(label = item['title'])
            if str(item['id']) not in cached_data:
                if progressbar is None:
                    progressbar = xbmcgui.DialogProgress()
                    progressbar.create('Stahování detailních dat')
                progressbar.update(round(i/count*100), str(i) + ' z ' + str(count))
                time.sleep(0.5)
                info = get_details(item['id'])
                info['image'] = item['images_hover'][0]
                info['poster'] = item['image_vertical']
                cached_data.update({str(item['id']) : info})
            list_item = set_list_item(list_item, info = cached_data[str(item['id'])])
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
            url = get_url(action='list_streams', label = label, page = int(next), id = id, type = type)  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        save_cache(data = cached_data)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)    

def list_categories(label):
    data = call_api(api = '/show/categories/', data = None)
    for item in data:
        list_item = xbmcgui.ListItem(label = item['title'])
        list_item.setInfo('video', {'plot': item['description']})
        url = get_url(action='list_streams', label = 'Kategorie / ' + item['title'], page = 1, id = item['id'], type = None)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

def list_recommended(label):
    cached_data = load_cache()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    data = call_api(api = '/show/recommended/', data = None)
    for item in data:
        list_item = xbmcgui.ListItem(label = item['title'])
        if str(item['id']) not in cached_data:
            info = get_details(item['id'])
            info['image'] = item['images_hover'][0]
            info['poster'] = item['image_vertical']
            cached_data.update({str(item['id']) : info})
        list_item = set_list_item(list_item, info = cached_data[str(item['id'])])
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
        save_cache(data = cached_data)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)    

def list_series(id, label):
    global token
    token =  get_token()
    cached_data = load_cache()
    if str(id) not in cached_data:
        info = get_details(int(id))
        cached_data.update({str(id) : info})
    save_cache(cached_data)
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    data = call_api(api = '/show/shows/' + str(id) + '/', data = None)
    for season in data['seasons']:
        dil = 0
        for episode in season['episodes']:
            dil += 1
            list_item = xbmcgui.ListItem(label = episode['title'] + ' (' + str(dil) + ')')
            list_item = set_list_item(list_item = list_item, info = cached_data[str(id)])
            list_item.setInfo('video', {'mediatype' : 'movie'})
            list_item.setInfo('video', {'plot': episode['synopsis']})
            if 'images_hover' in episode and len(episode['images_hover']) > 0:
                list_item.setArt({'thumb': episode['images_hover'][0]})
            if 'image_vertical' in episode and len(episode['image_vertical']) > 0:
                list_item.setArt({'poster': episode['image_vertical']})
            url = get_url(action='play_stream', id = episode['video'])  
            list_item.setInfo('video', {'duration': episode['length']})
            list_item.setProperty('IsPlayable', 'true')        
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

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
        cached_data = load_cache()
        for item in data['shows']:
            list_item = xbmcgui.ListItem(label = item['title'])
            if str(item['id']) not in cached_data:
                info = get_details(item['id'])
                info['image'] = item['images_hover'][0]
                info['poster'] = item['image_vertical']
                cached_data.update({str(item['id']) : info})
            list_item = set_list_item(list_item, info = cached_data[str(item['id'])])
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
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)    
        save_cache(data = cached_data)
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

def add_favourite(id):   
    global token
    token =  get_token()
    call_api(api = '/show/shows/' + str(id) + '/favourite/', method = 'PUT', data = None)
    xbmcgui.Dialog().notification('České kino','Přidáno do oblíbených', xbmcgui.NOTIFICATION_INFO, 3000)        
    xbmc.executebuiltin('Container.Refresh')

def remove_favourite(id):
    global token
    token =  get_token()
    call_api(api = '/show/shows/' + str(id) + '/favourite/', method = 'DELETE', data = None)
    xbmcgui.Dialog().notification('České kino','Odstraněno z oblíbených', xbmcgui.NOTIFICATION_INFO, 3000)        
    xbmc.executebuiltin('Container.Refresh')

def list_menu():
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')

    data = call_api(api = '/show/promo-categories/', data = None)
    for item in data:
        list_item = xbmcgui.ListItem(label = item['title'])
        url = get_url(action='list_streams', label = 'Kategorie / ' + item['title'], page = 1, id = item['id'], type = 'promo')  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Všechny')
    url = get_url(action='list_streams', label = 'Všechny', page = 1, id = None, type = None)  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'all.png'), 'icon' : os.path.join(icons_dir , 'all.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Kategorie')
    url = get_url(action='list_categories', label = 'Kategorie')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'categories.png'), 'icon' : os.path.join(icons_dir , 'categories.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Doporučené')
    url = get_url(action='list_recommended', label = 'Doporučené')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'recommended.png'), 'icon' : os.path.join(icons_dir , 'recommended.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Oblíbené')
    url = get_url(action='list_streams', label = 'Oblíbené', page = 1, id = None, type = 'favourites')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'favourites.png'), 'icon' : os.path.join(icons_dir , 'favourites.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Hledat')
    url = get_url(action='list_search', label = 'Hledat')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'search.png'), 'icon' : os.path.join(icons_dir , 'search.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)    

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_streams':
            list_streams(label = params['label'], page = params['page'], id = params['id'], type = params['type'])
        elif params['action'] == 'list_categories':
            list_categories(label = params['label'])
        elif params['action'] == 'play_stream':
            play_stream(id = params['id'])
        elif params['action'] == 'list_search':
            list_search(label = params['label'])
        elif params['action'] == 'list_search_results':
            list_search_results(query = params['query'], label = params['label'])
        elif params['action'] == 'list_series':
            list_series(id = params['id'], label = params['label'])
        elif params['action'] == 'list_recommended':
            list_recommended(label = params['label'])
        elif params['action'] == 'add_favourite':
            add_favourite(id = params['id'])
        elif params['action'] == 'remove_favourite':
            remove_favourite(id = params['id'])
        elif params['action'] == 'reset_session':
            remove_session()
        elif params['action'] == 'reset_cache':
            reset_cache()
        else:
            raise ValueError('Neznámý parametr: {0}!'.format(paramstring))
    else:
         list_menu()

if __name__ == '__main__':
    router(sys.argv[2][1:])
