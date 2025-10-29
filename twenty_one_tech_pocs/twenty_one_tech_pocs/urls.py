"""
URL configuration for twenty_one_tech_pocs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse


def robots_txt(request):
    return HttpResponse("User-agent: *\\nDisallow: /", content_type="text/plain")


urlpatterns = [
    path("robots.txt", robots_txt),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("", lambda request: HttpResponse(status=204)),
    path('admin/', admin.site.urls),
    path('api/equipment-entries/', include('twenty_one_tech_pocs.equipment_entry_app.urls')),
    path('api/maintenance/', include('twenty_one_tech_pocs.maintenance_assistant.urls')),
    path('api/service-manuals/', include('twenty_one_tech_pocs.service_manuals_assistant.urls')),
    path('api/safety-procedures/', include('twenty_one_tech_pocs.safety_procedure_assistant.urls')),
    path('api/training-manuals/', include('twenty_one_tech_pocs.training_manuals_assistant.urls')),
]
