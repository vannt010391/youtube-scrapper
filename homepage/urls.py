from django.urls import path
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('getdata/', views.get_data),
    path('download/', views.download_file)


]