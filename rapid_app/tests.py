# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
from django.test import TestCase
from rapid_app import settings_app
from rapid_app.models import RapidFileGrabber, RapidFileProcessor, RowFixer


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

    # end class RapidFileGrabberTest


class RapidFileProcessorTest( TestCase ):
    """ Tests models.RapidFileProcessor """

    def setUp( self ):
        """ Runs initialization. """
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

    def test__extract_print_holdings( self ):
        """ Tests filtering and parsing of records for easyAccess db. """
        self.assertEqual(
            {u'00029483qs1SIZEGN1A55': {
                u'call_number': '1-SIZE GN1 .A55',
                u'issn': '0002-9483',
                u'location': 'qs',
                u'years': ['1919']},
             u'00029629sciR11A6': {
                u'call_number': 'R11 .A6',
                u'issn': '0002-9629',
                u'location': 'sci',
                u'years': ['1926', '1928']},
             u'0022197XrsmchJX1C58': {
                u'call_number': 'JX1 .C58',
                u'issn': '0022-197X',
                u'location': 'rsmch',
                u'years': ['1991', '1992']},
             u'00318701sciTR1P58': {
                u'call_number': 'TR1 .P58',
                u'issn': '0031-8701',
                u'location': 'sci',
                u'years': ['1962']},
             u'00802042qsQP1E7': {
                u'call_number': 'QP1 .E7',
                u'issn': '0080-2042',
                u'location': 'qs',
                u'years': ['1937', '1938']},
             u'04927079sci1SIZETN24T2A2': {
                u'call_number': '1-SIZE TN24.T2 A2',
                u'issn': '0492-7079',
                u'location': 'sci',
                u'years': ['1971']}},
            self.processor.extract_print_holdings()
            )

    def test__contigify_list( self ):
        """ Tests updating list of single elements to list of lists-of-contiguous elements. """
        start_lst = [ 1, 2, 4, 5, 7 ]
        self.assertEqual(
            [ [1, 2], [4, 5], [7] ],
            self.processor._contigify_list( start_lst )
            )
        start_lst = [ '1', '2', '4', '5', '7' ]
        self.assertEqual(
            [ [1, 2], [4, 5], [7] ],
            self.processor._contigify_list( start_lst )
            )

    def test__build_years_held( self ):
        """ Tests converting contig list to list of start-end dcts. """
        contig_list = [ [1, 2], [4, 5], [7] ]
        self.assertEqual(
            [
                {u'start': 1, u'end': 2},
                {u'start': 4, u'end': 5},
                {u'start': 7, u'end': 7}],
            self.processor._build_years_held( contig_list )
            )

    def test__build_holdings_lst( self ):
        """ Tests conversion of holdings_dct to holdings_lst. """
        holdings_dct = {
             u'00029483qs1SIZEGN1A55': {
                u'call_number': '1-SIZE GN1 .A55',
                u'issn': '0002-9483',
                u'location': 'qs',
                u'years': ['1919']},
             u'00029629sciR11A6': {
                u'call_number': 'R11 .A6',
                u'issn': '0002-9629',
                u'location': 'sci',
                u'years': ['1926', '1928']},
             u'0022197XrsmchJX1C58': {
                u'call_number': 'JX1 .C58',
                u'issn': '0022-197X',
                u'location': 'rsmch',
                u'years': ['1991', '1992']},
             u'00318701sciTR1P58': {
                u'call_number': 'TR1 .P58',
                u'issn': '0031-8701',
                u'location': 'sci',
                u'years': ['1962']},
             u'00802042qsQP1E7': {
                u'call_number': 'QP1 .E7',
                u'issn': '0080-2042',
                u'location': 'qs',
                u'years': ['1937', '1938']},
             u'04927079sci1SIZETN24T2A2': {
                u'call_number': '1-SIZE TN24.T2 A2',
                u'issn': '0492-7079',
                u'location': 'sci',
                u'years': ['1971']}
            }
        self.assertEqual(
            [[u'000294831919', u'0002-9483', u'qs', u'1-SIZE GN1 .A55', 1919, 1919],
             [u'000296291926', u'0002-9629', u'sci', u'R11 .A6', 1926, 1926],
             [u'000296291928', u'0002-9629', u'sci', u'R11 .A6', 1928, 1928],
             [u'0022197X1991', u'0022-197X', u'rsmch', u'JX1 .C58', 1991, 1992],
             [u'003187011962', u'0031-8701', u'sci', u'TR1 .P58', 1962, 1962],
             [u'008020421937', u'0080-2042', u'qs', u'QP1 .E7', 1937, 1938],
             [u'049270791971', u'0492-7079', u'sci', u'1-SIZE TN24.T2 A2', 1971, 1971]],
            self.processor.build_holdings_lst( holdings_dct )
            )

    # end class RapidFileProcessorTest


class RowFixerTest( TestCase ):
    """ Tests models.RowFixer """

    def setUp( self ):
        """ Runs initialization. """
        self.defs_dct = {  # proper row field-definitions
            'library': 0 ,
            'branch': 1,
            'location': 2,
            'callnumber': 3,
            'title': 4,
            'format': 5,
            'issn_num': 6,
            'issn_type': 7,
            'vol_start': 8,
            'vol_end': 9,
            'year': 10
            }
        self.fixer = RowFixer( self.defs_dct )

    def test__fix_row( self ):
        """ Tests filtering and parsing of records for easyAccess db. """
        bad_string = 'RBN,Main Library,qs,QP1 .E7,Ergebnisse der Physiologie, biologischen Chemie und experimentellen Pharmakologie. Reviews of physiology, biochemistry, and experimental pharmacology,Print,0080-2042,ISSN,1,69,1937'
        bad_row = bad_string.split( ',' )
        self.assertEqual(
            [u'RBN', u'Main Library', u'qs', u'QP1 .E7', u'Ergebnisse der Physiologie biologischen Chemie und experimentellen Pharmakologie. Reviews of physiology, biochemistry, and experimental pharmacology', u'Print', u'0080-2042', u'ISSN', u'1', u'69', u'1937'],
            self.fixer.fix_row( bad_row )
            )

    # end class RowFixerTest


## end ##
