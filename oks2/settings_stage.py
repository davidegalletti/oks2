#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .settings import *
from .keep_safe import STAGE_SECRET_KEY, STAGE_DATABASE_NAME

SECRET_KEY = STAGE_SECRET_KEY
DATABASES['default']['NAME'] = STAGE_DATABASE_NAME
