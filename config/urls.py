# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView

admin.autodiscover()


urlpatterns = patterns('',

    url( r'^admin/', include(admin.site.urls) ),

    url( r'^info/$',  'rapid_app.views.hi', name='info_url' ),

    url( r'^tasks/$',  'rapid_app.views.tasks', name='tasks_url' ),

    url( r'^tasks/process_file_from_rapid/$',  'rapid_app.views.process_file_from_rapid', name='process_file_from_rapid_url' ),

    url( r'^tasks/update_titles_table/$',  'rapid_app.views.update_titles', name='update_titles_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    )


# urlpatterns = patterns('',

#     url( r'^admin/', include(admin.site.urls) ),

#     url( r'^', include('rapid_app.urls_app') ),

# )
