# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
from django.http import HttpResponse
from django.shortcuts import render
from ks.models import this_ks


def home(request):
    cont = {'this_ks': this_ks, 'this_ks_encoded_url': this_ks.url(True)}
    return render(request, 'ks/home.html', cont)


def debug(request):
    '''
    created to debug code

    Args:
        request:
    '''
    return HttpResponse( "Debug")


