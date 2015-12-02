# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.test import TestCase
from rapid_app import settings_app
from rapid_app.models import RapidFileGrabber


class RapidFileGrabberTest( TestCase ):
    """ Tests models.RapidFileGrabber() """

    def test__grab_file( self ):
        """ Tests grab of remote file. """
        grabber = RapidFileGrabber(
            settings_app.TEST_REMOTE_SERVER_NAME,
            settings_app.TEST_REMOTE_SERVER_PORT,
            settings_app.TEST_REMOTE_SERVER_USERNAME,
            settings_app.TEST_REMOTE_SERVER_PASSWORD,
            settings_app.TEST_REMOTE_FILEPATH,
            ""
            )
        self.assertEqual(
            42,
            grabber.grab_file() )
