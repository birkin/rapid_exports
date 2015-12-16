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

## DB MANUAL ACCESS ##

## dev db ##
DEV_DB_HOST = unicode( os.environ['RAPID__DEV_DB_HOST'] )
DEV_DB_USER = unicode( os.environ['RAPID__DEV_DB_USER'] )
DEV_DB_PASSWORD = unicode( os.environ['RAPID__DEV_DB_PASSWORD'] )

## prod db ##
PROD_DB_HOST = unicode( os.environ['RAPID__PROD_DB_HOST'] )
PROD_DB_USER = unicode( os.environ['RAPID__PROD_DB_USER'] )
PROD_DB_PASSWORD = unicode( os.environ['RAPID__PROD_DB_PASSWORD'] )

## either db ##
DB_NAME = unicode( os.environ['RAPID__DB_NAME'] )
DB_TABLE = unicode( os.environ['RAPID__DB_TABLE'] )
DB_CONDITIONAL_INSERT_SQL_PATTERN = unicode( os.environ['RAPID__DB_CONDITIONAL_INSERT_SQL_PATTERN'] )
DB_CONDITIONAL_DELETE_SQL_PATTERN = unicode( os.environ['RAPID__DB_CONDITIONAL_DELETE_SQL_PATTERN'] )

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


## end ##
