from django.contrib import admin
from .models import YoutubeAPI

# Register your models here.
@admin.register(YoutubeAPI)
class YoutubeAPIAdmin(admin.ModelAdmin):
    list_display = ['title', 'api_key', 'create', 'update']

