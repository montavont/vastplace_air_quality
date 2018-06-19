# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.utils import OperationalError
from django.apps import AppConfig

AMBASSADAIR_TYPE_STATIC = "ambassadair_static"
AMBASSADAIR_TYPE_MOBILE = "ambassadair_mobile"


class AmbassadairConfig(AppConfig):
    name = 'experiments.vastplace_ambassadair'
    def ready(self):
        from campaignfiles.models import SourceType
        try:
            SourceType.objects.get_or_create(sourceType = AMBASSADAIR_TYPE_MOBILE, module = "experiments.vastplace_ambassadair", parserClass = "csv_parser")
            SourceType.objects.get_or_create(sourceType = AMBASSADAIR_TYPE_STATIC, module = "experiments.vastplace_ambassadair", parserClass = "csv_parser")
        except OperationalError:
            print "OperationalError while importing"
            pass

