# -*- coding: utf-8 -*-
import xbmc
import xbmcgui

from libs.api import call_api
from libs.session import get_token

def add_favourite(id):   
    call_api(api = '/show/shows/' + str(id) + '/favourite/', method = 'PUT', data = None, token = get_token())
    xbmcgui.Dialog().notification('České kino','Přidáno do oblíbených', xbmcgui.NOTIFICATION_INFO, 3000)        
    xbmc.executebuiltin('Container.Refresh')

def remove_favourite(id):
    call_api(api = '/show/shows/' + str(id) + '/favourite/', method = 'DELETE', data = None, token = get_token())
    xbmcgui.Dialog().notification('České kino','Odstraněno z oblíbených', xbmcgui.NOTIFICATION_INFO, 3000)        
    xbmc.executebuiltin('Container.Refresh')
