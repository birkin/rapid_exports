# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs, csv, datetime, itertools, json, logging, os, pprint, shutil
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect
from django.utils.encoding import smart_unicode
from django.utils.text import slugify

log = logging.getLogger(__name__)


class RapidFileGrabber( object ):
    """ Access Rapid's prepared file.
        Not-django class. """

    def __init__( self, remote_server_name, remote_server_username, remote_server_password, remote_filepath, local_destination_filepath ):
        self.remote_server_name = remote_server_name
        self.remote_server_username = remote_server_username
        self.remote_server_password = remote_server_password
        self.remote_filepath = remote_filepath
        self.local_destination_filepath = local_destination_filepath

    def grab_file( self ):
        """ Grabs file.
            Will be called via view. """
        log.debug( 'starting grab_file()' )
        return 'foo'

    # end class RapidFileGrabber


class RapidProcessor( object ):
    """ Handles processing of file from Rapid.
        Non-django class. """

    def __init__(self):
        self.from_rapid_filepath = unicode( os.environ['RAPID__FROM_RAPID_FILEPATH'] )  # actual initial file from rapid
        self.from_rapid_temp_filepath = unicode( os.environ['RAPID__FROM_RAPID_TEMP_FILEPATH'] )  # temp path in case we need to convert original file to utf8
        self.print_dct = {}

    def parse_file_from_rapid( self ):
        """ Extracts print holdings from the file-from-rapid.
            That file contains both print and online holdings.
            Will be called via view. """
        if self.check_utf8() is False:
            self.make_utf8()

    def check_utf8( self ):
        """ Ensures file is utf-8 readable.
            Will error and return False if not.
            Called by parse_file_from_rapid() """
        utf8 = False
        with codecs.open( self.from_rapid_filepath, 'rb', 'utf-8' ) as myfile:
            try:
                for line in myfile:  # reads line-by-line; doesn't tax memory on big files
                    pass
                utf8 = True
            except Exception as e:
                # log.debug( 'exception, `%s`' % e )
                print 'exception, `%s`' % e
        return utf8

    def make_utf8( self ):
        """ Iterates through each line; ensures it can be converted to utf-8.
            Called by parse_file_from_rapid() """
        shutil.copy( self.from_rapid_filepath, '%s.backup' % self.from_rapid_filepath )  # backing up (from, to)
        with codecs.open( self.from_rapid_filepath, 'rb', 'utf-16' ) as input_file:
            with open( self.from_rapid_temp_filepath, 'wb' ) as output_file:
                for line in input_file:
                    assert( type(line) == unicode )
                    try:
                        output_file.write( line.encode('utf-8') )
                    except Exception as e:
                        print '- error, `%s`; line, `%s`' % ( unicode(repr(e)), unicode(repr(line)) )
        shutil.move( self.from_rapid_temp_filepath, self.from_rapid_filepath )  # (from, to)
        return

    # end class RapidProcessor
