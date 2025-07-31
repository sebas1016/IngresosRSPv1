"""
URL configuration for ingresosRSP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from gestion.views import login_personalizado as Login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion.urls'), name='gestion'),
    path('login/', Login,name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
