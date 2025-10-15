"""
a module to give information about korpy
"""
import os
import urllib.request

def get_release_note(version: str) -> str:
    if not os.path.exists('release_note.rst'):
        urllib.request.urlretrieve('https://github.com/MatthewKim12/korpy/blob/main/HISTORY.rst', 'release_note.rst')
    with open('release_note.rst', 'rb') as f:
        release_note = f.read().decode('utf-8')
        filtered = release_note.replace('\n======\n', '\n').replace('- ', '')
    return filtered