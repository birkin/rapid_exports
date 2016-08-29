# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib import admin
from rapid_app.models import PrintTitleDev, ProcessorTracker


class PrintTitleDevAdmin( admin.ModelAdmin ):
    ordering = [ 'key' ]
    date_hierarchy = 'date_updated'
    list_display = [
        'key', 'issn', 'start', 'end', 'call_number', 'building', 'location', 'title', 'date_updated' ]
    search_fields = list_display
    # readonly_fields = list_display
    list_filter = [ 'building', 'location', 'title', 'issn' ]


class ProcessorTrackerAdmin( admin.ModelAdmin ):
    list_display = [
        'current_status', 'processing_started', 'procesing_ended', 'recent_processing' ]
    readonly_fields = list_display


admin.site.register( PrintTitleDev, PrintTitleDevAdmin )
admin.site.register( ProcessorTracker, ProcessorTrackerAdmin )
