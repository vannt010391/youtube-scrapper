from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from .models import YoutubeAPI
import json
import requests
from tqdm import tqdm
import asyncio, sys
from subprocess import run, PIPE


import  mimetypes, os


# Create your views here.
def homepage(request):
    return render(request, 'homepage/homepage.html')
       

def get_data(request):
    data = YoutubeAPI.objects.all()
    data = data.values()
    youtube_api = data[0]['api_key'] 
    channel_name = request.POST.get('channel_name')
    request.session['channel_name'] = channel_name
    out = run([sys.executable, 'G:\\___epikla\\youtube-scrapper-project\\yt_stats2.py', youtube_api, channel_name], shell=False, stdout=PIPE)
    output = "Completed Process. Your file is: " + channel_name +'.csv'
    request.session['channel_name'] = channel_name
    return render(request, 'homepage/data.html', {'data': output})


def download_file(request):
    data = request.session['channel_name']
    filename = data + '.csv'
    if filename != '':
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = BASE_DIR + '/' + filename
        path = open(filepath, 'rb')
        mime_type, _ = mimetypes.guess_type(filepath)
        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    else:
        return render(request, 'homepage/homepage.html')
            
    










