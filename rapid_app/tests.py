# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
from django.test import TestCase
from rapid_app import settings_app
from rapid_app.models import RapidFileGrabber, RapidFileProcessor


class RapidFileGrabberTest( TestCase ):
    """ Tests models.RapidFileGrabber() """

    def setUp( self ):
        """ Runs initialization; ensures test-file doesn't exist locally. """
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
            2277,  # bytes
            os.path.getsize(settings_app.TEST_LOCAL_DESTINATION_FILEPATH) )

    def test__unzip_file( self ):
        """ Tests unzip of downloaded file. """
        self.grabber.local_destination_filepath = settings_app.TEST_ZIPFILE_FILEPATH  # rapid_app/test_files/test_RBNextract.zip
        self.grabber.unzip_file()
        self.assertEqual(
            20576,  # bytes
            os.path.getsize('%s/%s' % (settings_app.TEST_ZIPFILE_EXTRACT_DIR_PATH, settings_app.TEST_ZIPFILE_EXTRACT_FILENAME)) )

    def tearDown( self ):
        """ Removes downloaded test-file. """
        if os.path.isfile( settings_app.TEST_LOCAL_DESTINATION_FILEPATH ):
            os.remove( settings_app.TEST_LOCAL_DESTINATION_FILEPATH )

    # end RapidFileGrabberTest


class RapidFileProcessorTest( TestCase ):
    """ Tests models.RapidFileProcessor """

    def setUp( self ):
        """ Runs initialization; ensures test-file doesn't exist locally. """
        self.processor = RapidFileProcessor(
            settings_app.TEST_FROM_RAPID_FILEPATH,
            settings_app.TEST_FROM_RAPID_UTF8_FILEPATH,
            )

    def test__check_utf8_before( self ):
        """ Tests detection of non-utf8 data. """
        self.assertEqual(
            False,
            self.processor.check_utf8()
            )

    def test__check_utf8_after( self ):
        """ Tests detection of utf8 data. """
        self.processor.make_utf8()
        self.assertEqual(
            True,
            self.processor.check_utf8( settings_app.TEST_FROM_RAPID_UTF8_FILEPATH )
            )

## end ##
