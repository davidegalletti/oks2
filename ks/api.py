# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import json
from datetime import datetime
from django.urls import reverse
from urllib.request import urlopen

from ks.utils import KsUrl


def json_serial(obj):
    """
        JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


class ApiInvoker:
    def __init__(self, outcome=None, request_format=None):
        self.outcome = outcome
        self.request_format = request_format

    def invoke(self, remote_url):
        response = urlopen(remote_url)
        self.response = response.read().decode("utf-8")
        self.parse(self.response)


class Api:
    success = "success"
    failure = "failure"

    def __init__(self, outcome="", message="", content="", request=None, format='json',
                 datetime_generated_utc=datetime.utcnow(), deprecated=False, deprecation_message=""):
        self.outcome = outcome

        self.message = message
        self.request = request
        self.format = format
        self.content = content
        self.response = ""
        self.datetime_generated_utc = datetime_generated_utc
        self.deprecated = deprecated
        self.deprecation_message = deprecation_message

    def urlopen(self, remote_url):
        response = urlopen(remote_url)
        self.response = response.read().decode("utf-8")
        self.parse(self.response)

    @property
    def response_format(self):
        if self.format:
            return self.format
        if self.request:
            # we try the GET parameter first
            if 'format' in self.request.GET.keys():
                return self.request.GET['format'].upper()
            try:
                accept_header = self.request.META['HTTP_ACCEPT']
                if accept_header == 'application/json':
                    return 'JSON'
                #                 elif accept_header == 'application/xml':
                #                     return 'XML'
                elif accept_header[:9] == 'text/html':
                    # 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    return 'HTML'
            except Exception as e:
                return Api.default_format
        else:
            return Api.default_format

    def invoke_oks_api(self, oks, api):
        oks_url = KsUrl(oks)
        local_url = reverse(api)
        self.urlopen(oks_url.home() + local_url)

    def json(self):
        #         if self.deprecated:
        #             ret_str +=  '", "deprecated" : "' + self.deprecation_message
        return json.dumps({"status": self.status, "message": self.message,
                           "datetime_generated_utc": self.datetime_generated_utc.isoformat(),
                           "content": self.content}, sort_keys=False, default=json_serial)

    def parse(self, json_response):
        self.response = json_response
        decoded = json.loads(self.response)
        self.status = decoded['status']
        self.message = decoded['message']
        self.content = decoded['content']
