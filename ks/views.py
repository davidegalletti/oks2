# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
from django.http import HttpResponse
from django.shortcuts import render


def debug(request):
    '''
    created to debug code

    Args:
        request:
    '''
    return HttpResponse( "Debug")


def home(request):
    '''
    created to debug code

    Args:
        request:
    '''
    return HttpResponse( "Home")