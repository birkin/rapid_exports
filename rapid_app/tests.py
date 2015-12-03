# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
from django.test import TestCase
from rapid_app import settings_app
from rapid_app.models import RapidFileGrabber


class RapidFileGrabberTest( TestCase ):
    """ Tests models.RapidFileGrabber() """

    def setUp( self ):
        """ Ensures test-file doesn't exist locally. """
        assert os.path.isfile( settings_app.TEST_LOCAL_DESTINATION_FILEPATH ) == False
        self.grabber = RapidFileGrabber(
            settings_app.TEST_REMOTE_SERVER_NAME,
            settings_app.TEST_REMOTE_SERVER_USERNAME,
            settings_app.TEST_REMOTE_SERVER_PASSWORD,
            settings_app.TEST_REMOTE_FILEPATH,
            settings_app.TEST_LOCAL_DESTINATION_FILEPATH,
            settings_app.TEST_ZIPFILE_EXTRACT_DIR_PATH,
            )

    def test__grab_file( self ):
        """ Tests grab of remote file. """
        self.grabber.grab_file()
        self.assertEqual(
            48662430,  # bytes
            os.path.getsize(settings_app.TEST_LOCAL_DESTINATION_FILEPATH) )

    def test__unzip_file( self ):
        """ Tests unzip of downloaded file. """
        self.grabber.local_destination_filepath = settings_app.TEST_ZIPFILE_FILEPATH
        self.grabber.unzip_file()
        self.assertEqual(
            718576792,  # bytes
            os.path.getsize('%s/%s' % (settings_app.TEST_ZIPFILE_EXTRACT_DIR_PATH, settings_app.TEST_ZIPFILE_EXTRACT_FILENAME)) )

    def tearDown( self ):
        """ Removes downloaded test-file. """
        if os.path.isfile( settings_app.TEST_LOCAL_DESTINATION_FILEPATH ):
            os.remove( settings_app.TEST_LOCAL_DESTINATION_FILEPATH )

    # end RapidFileGrabberTest
