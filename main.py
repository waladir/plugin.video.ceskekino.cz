# -*- coding: utf-8 -*-
import sys

from urllib.parse import parse_qsl

from libs.session import remove_session
from libs.lists import list_menu, list_streams, list_categories, list_series
from libs.stream import play_stream
from libs.search import list_search, list_search_results
from libs.favourites import add_favourite, remove_favourite
from libs.data import reset_cache

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_streams':
            list_streams(label = params['label'], page = params['page'], category_id = params['category_id'], type = params['type'])
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
