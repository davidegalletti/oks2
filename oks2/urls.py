# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ks/', include('ks.urls')),
    path('', RedirectView.as_view(pattern_name='home', permanent=True)),
    #    path('api/', 'ks.api', 'ks'),
]
