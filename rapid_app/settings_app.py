# -*- coding: utf-8 -*-

from __future__ import unicode_literals

""" `rapid_app` settings """

import os


TEST_REMOTE_SERVER_NAME = unicode( os.environ['RAPID__TEST_REMOTE_SERVER_NAME'] )
TEST_REMOTE_SERVER_USERNAME = unicode( os.environ['RAPID__TEST_REMOTE_SERVER_USERNAME'] )
TEST_REMOTE_SERVER_PASSWORD = unicode( os.environ['RAPID__TEST_REMOTE_SERVER_PASSWORD'] )
TEST_REMOTE_FILEPATH = unicode( os.environ['RAPID__TEST_REMOTE_FILEPATH'] )
TEST_LOCAL_DESTINATION_FILEPATH = unicode( os.environ['RAPID__TEST_LOCAL_DESTINATION_FILEPATH'] )
