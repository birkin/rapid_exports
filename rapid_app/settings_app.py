# -*- coding: utf-8 -*-

from __future__ import unicode_literals

""" `rapid_app` settings """

import os


## grab file ##
REMOTE_SERVER_NAME = unicode( os.environ['RAPID__REMOTE_SERVER_NAME'] )
REMOTE_SERVER_USERNAME = unicode( os.environ['RAPID__REMOTE_SERVER_USERNAME'] )
REMOTE_SERVER_PASSWORD = unicode( os.environ['RAPID__REMOTE_SERVER_PASSWORD'] )
REMOTE_FILEPATH = unicode( os.environ['RAPID__REMOTE_FILEPATH'] )
LOCAL_DESTINATION_FILEPATH = unicode( os.environ['RAPID__LOCAL_DESTINATION_FILEPATH'] )
#
ZIPFILE_EXTRACT_DIR_PATH = unicode( os.environ['RAPID__ZIPFILE_EXTRACT_DIR_PATH'] )
ZIPFILE_EXTRACT_FILENAME = unicode( os.environ['RAPID__ZIPFILE_EXTRACT_FILENAME'] )

## process ##
FROM_RAPID_FILEPATH = '%s/%s' % ( ZIPFILE_EXTRACT_DIR_PATH, ZIPFILE_EXTRACT_FILENAME )
FROM_RAPID_UTF8_FILEPATH = unicode( os.environ['RAPID__FROM_RAPID_UTF8_FILEPATH'] )
LOCATIONS_URL = unicode( os.environ['RAPID__LOCATIONS_JSON_URL'] )

## DB MANUAL ACCESS ##

## update production db ##
DB_CONNECTION_URL = unicode( os.environ['RAPID__MANUAL_DB_CONNECTION_URL'] )
DB_TITLES_TABLE = unicode( os.environ['RAPID__TITLES_TABLE_NAME'] )


###########
## TESTS ##
###########

## grab file ##
TEST_REMOTE_SERVER_NAME = unicode( os.environ['RAPID__TEST_REMOTE_SERVER_NAME'] )
TEST_REMOTE_SERVER_USERNAME = unicode( os.environ['RAPID__TEST_REMOTE_SERVER_USERNAME'] )
TEST_REMOTE_SERVER_PASSWORD = unicode( os.environ['RAPID__TEST_REMOTE_SERVER_PASSWORD'] )
TEST_REMOTE_FILEPATH = unicode( os.environ['RAPID__TEST_REMOTE_FILEPATH'] )
TEST_LOCAL_DESTINATION_FILEPATH = unicode( os.environ['RAPID__TEST_LOCAL_DESTINATION_FILEPATH'] )
#
TEST_ZIPFILE_FILEPATH = unicode( os.environ['RAPID__TEST_ZIPFILE_FILEPATH'] )
TEST_ZIPFILE_EXTRACT_DIR_PATH = unicode( os.environ['RAPID__TEST_ZIPFILE_EXTRACT_DIR_PATH'] )
TEST_ZIPFILE_EXTRACT_FILENAME = unicode( os.environ['RAPID__TEST_ZIPFILE_EXTRACT_FILENAME'] )

## process ##
TEST_FROM_RAPID_FILEPATH = unicode( os.environ['RAPID__TEST_FROM_RAPID_FILEPATH'] )
TEST_FROM_RAPID_UTF8_FILEPATH = unicode( os.environ['RAPID__TEST_FROM_RAPID_UTF8_FILEPATH'] )

## DB MANUAL ACCESS ##

## update production db ##
TEST_DB_CONNECTION_URL = unicode( os.environ['RAPID__TEST_MANUAL_DB_CONNECTION_URL'] )

## end ##
