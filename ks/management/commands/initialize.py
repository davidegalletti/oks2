# -*- coding: utf-8 -*-

import logging, os, urllib.request
from django.db import transaction
from django.core.management.base import BaseCommand
from ks.models import KnowledgeServer, Organization

logger = logging.getLogger(__name__)


def c4k_oks(db_alias):
    # this data must be created on the root ks but also on any other as it is essential for basic ks operation
    c4k_it = Organization()
    c4k_it.id = 1
    c4k_it.name = "C4K it"
    c4k_it.UKCL = "-"
    c4k_it.website = 'https://www.c4k.it'
    c4k_it.logo = 'https://www.c4k.it/logoc4kit.png'

    c4k_it.description = "The Knowledge Oriented Architecture organization."
    c4k_it.save(using=db_alias)

    c4k_it_ks = KnowledgeServer(pk=1, name="Root Open Knowledge Server", scheme="http",
                                netloc="root.c4k.it",
                                stage_netloc="root.stage.c4k.it",
                                description="The Open Knowledge Server serving the structures and datasets used by any other Knowledge Server.",
                                organization=c4k_it, this_ks=True, html_home="root html_home",
                                html_disclaimer="root html_disclaimer")
    c4k_it_ks.save(using=db_alias)


class Command(BaseCommand):
    help = ''' Some fixture oks_root specific???? '''

    def add_arguments(self, parser):
        parser.add_argument(
            'db_alias', nargs='?',
            help="db_alias",
        )
        parser.add_argument(
            'root', nargs='?',
            help="1 for rootoks.c4k.org, any other value or no value not root",
        )

    def handle(self, *args, **options):
        db_alias = 'default'
        if db_alias in options:
            db_alias = options['db_alias']
        c4k_oks(db_alias)
        # license()
        logger.info("END END END fixture END END END")
