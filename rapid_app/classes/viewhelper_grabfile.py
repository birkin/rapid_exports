# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from rapid_app import settings_app
from rapid_app.models import RapidFileGrabber  # TODO: move this to classes dir


class GrabFileFromRapid( object ):
    """ Manages views.grab_file_from_rapid() work.
        TODO; view not yet implemented. """

    def _setup_grabber( self ):
        """ Initializes grabber.
            Called by initiate_work() """
        grabber = RapidFileGrabber(
            settings_app.REMOTE_SERVER_NAME,
            settings_app.REMOTE_SERVER_USERNAME,
            settings_app.REMOTE_SERVER_PASSWORD,
            settings_app.REMOTE_FILEPATH,
            settings_app.LOCAL_DESTINATION_FILEPATH,
            settings_app.ZIPFILE_EXTRACT_DIR_PATH,
            )
        return grabber

    # end class GrabFileFromRapid
