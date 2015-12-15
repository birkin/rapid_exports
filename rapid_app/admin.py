# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib import admin
from rapid_app.models import PrintTitleDev


class PrintTitleDevAdmin( admin.ModelAdmin ):
    ordering = [ 'key' ]
    date_hierarchy = 'date_updated'
    list_display = [
        'key', 'issn', 'start', 'end', 'location', 'call_number', 'date_updated' ]
    search_fields = list_display
    readonly_fields = list_display

    # end class


admin.site.register( PrintTitleDev, PrintTitleDevAdmin )
