#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
from .settings import *
from .keep_safe import STAGE_SECRET_KEY

SECRET_KEY = STAGE_SECRET_KEY
DATABASES['default']['NAME'] = 'oks_root_stage'
