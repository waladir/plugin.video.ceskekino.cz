# -*- coding: utf-8 -*-
import os
import sys

import xbmcgui
import xbmcaddon
from xbmcvfs import translatePath

import json
import codecs
import time

from libs.api import call_api

def get_token():
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
        data = call_api(api = '/account/profiles/', data = None, token = token)
        id = -1
        if len(data) > 0:
            id = data[0]['id']
        data = call_api(api = '/account/login-profile/' + str(id) + '/', data = None, method = 'POST', token = token)
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
