#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .settings_base import *
from .keep_safe import SECRET_KEY as SAFE_SECRET_KEY, DATABASE_PASSWORD, DATABASE_NAME


SECRET_KEY = SAFE_SECRET_KEY
DATABASES['default']['NAME'] = DATABASE_NAME
DATABASES['default']['PASSWORD'] = DATABASE_PASSWORD
