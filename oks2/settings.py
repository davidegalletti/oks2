#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
from .settings_base import *
from .keep_safe import SECRET_KEY as SAFE_SECRET_KEY, DATABASE_PASSWORD


SECRET_KEY = SAFE_SECRET_KEY
DATABASES['default']['NAME'] = 'oks_root'
DATABASES['default']['USER'] = 'oks'
DATABASES['default']['PASSWORD'] = DATABASE_PASSWORD
