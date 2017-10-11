import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from subprocess import call
import os
import base64
from django.http import HttpResponse, JsonResponse
from django_test.settings import BASE_DIR

from .music_maker import music_maker

# Create your views here.
def index(request):
    # python_cmd = 'python2'
    python_cmd = 'C:\\Python27\\python.exe'

    script = BASE_DIR + '/data_music/music_maker/music_maker.py'

    print(python_cmd)
    print(call([python_cmd, script ]))
    with open(BASE_DIR + '/data_music/music_maker/test.midi', 'rb') as midi_file:
        encoded_file = base64.b64encode(midi_file.read())

    return HttpResponse(encoded_file)

@csrf_exempt
def neighborhood_music(request):
    data = json.loads(request.body)
    hood = data['hood']
    tracks = data['tracks']

    print(hood)
    print(tracks)
    b64_music = music_maker.make_nhood_music(hood, tracks)

    return JsonResponse({'music': b64_music})


