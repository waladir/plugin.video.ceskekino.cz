# -*- coding: utf-8 -*-
import os
import sys

import xbmc
import xbmcgui
import xbmcaddon
from xbmcvfs import translatePath

import json
import codecs
import time
from urllib.request import urlopen

from libs.api import call_api
from libs.session import get_token
from libs.utils import get_kodi_version

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
    if len(data) == 0 or 'metadata' not in data or data['metadata']['valid_to'] < int(time.time()):
        data.update({'metadata' : {'valid_to' : int(time.time() + 60*60*24)}})
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
    data = call_api(api = '/show/shows/' + str(id) + '/', data = None, token = get_token())
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
    if get_kodi_version() >= 20:
        infotag = list_item.getVideoInfoTag()
        infotag.setPlot(info['description'])
        if info['year'].isdigit():
            infotag.setYear(int(info['year']))
        infotag.setCountries([info['country']])
        for genre in info['genres']:      
            genres.append(genre)
        infotag.setGenres(genres)
        if len(info['cast']) > 0:
            for person in info['cast']:      
                cast.append(xbmc.Actor(person))
            infotag.setCast(cast)
        if len(info['directors']) > 0:
            for person in info['directors']:      
                directors.append(person)
            infotag.setDirectors(directors)
        if 'duration' in info:
            infotag.setDuration(int(info['duration']))
        list_item.setArt({'thumb': info['image']})
        list_item.setArt({'poster': info['poster']})
        if 'rating' in info:
            infotag.setRating(round(float(info['rating'])/10, 1))
    else:
        list_item.setInfo('video', {'mediatype' : 'movie'})
        list_item.setInfo('video', {'plot': info['description']})
        if info['year'].isdigit():
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

