# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging, os, pprint
from django.test import TestCase
from rapid_app import settings_app
from rapid_app.lib.processor import HoldingsDctBuilder, RapidFileProcessor, RowFixer, Utf8Maker
from rapid_app.lib.ss_builder import SSBuilder
from rapid_app.models import RapidFileGrabber  # TODO: move to lib from models
from sqlalchemy import create_engine as alchemy_create_engine
from sqlalchemy.orm import sessionmaker as alchemy_sessionmaker, scoped_session as alchemy_scoped_session


log = logging.getLogger(__name__)
TestCase.maxDiff = None


class Utf8MakerTest( TestCase ):
    """ Tests models.Utf8Maker """

    def setUp( self ):
        """ Runs initialization. """
        self.utf8_maker = Utf8Maker(
            settings_app.TEST_FROM_RAPID_FILEPATH,
            settings_app.TEST_FROM_RAPID_UTF8_FILEPATH,
            )

    def test__check_utf8_before( self ):
        """ Tests detection of non-utf8 data. """
        self.assertEqual(
            False,
            self.utf8_maker.check_utf8()
            )

    def test__check_utf8_after( self ):
        """ Tests detection of utf8 data. """
        self.utf8_maker.make_utf8()
        self.assertEqual(
            True,
            self.utf8_maker.check_utf8( settings_app.TEST_FROM_RAPID_UTF8_FILEPATH )
            )

    # end class Utf8MakerTest


class RapidFileProcessorTest( TestCase ):
    """ Tests models.RapidFileProcessor """

    def setUp( self ):
        """ Runs initialization. """
        self.processor = RapidFileProcessor(
            settings_app.TEST_FROM_RAPID_FILEPATH,
            settings_app.TEST_FROM_RAPID_UTF8_FILEPATH,
            )

    def test__contigify_list( self ):
        """ Tests updating list of single elements to list of lists-of-contiguous elements. """
        start_lst = [ 1, 2, 3, 5, 6, 8 ]
        self.assertEqual(
            [ [1, 2, 3], [5, 6], [8] ],
            self.processor._contigify_list( start_lst )
            )
        start_lst = [ '1', '2', '4', '5', '7' ]
        self.assertEqual(
            [ [1, 2], [4, 5], [7] ],
            self.processor._contigify_list( start_lst )
            )

    def test__build_years_held( self ):
        """ Tests converting contig list to list of start-end dcts. """
        contig_list = [ [1, 2, 3], [5, 6], [8] ]
        self.assertEqual(
            [
                {u'start': 1, u'end': 3},
                {u'start': 5, u'end': 6},
                {u'start': 8, u'end': 8}],
            self.processor._build_years_held( contig_list )
            )

    def test__build_holdings_lst( self ):
        """ Tests conversion of holdings_dct to holdings_lst. """
        holdings_dct = {
             u'00029483qs1SIZEGN1A55': {
                u'building': 'foo',
                u'call_number': '1-SIZE GN1 .A55',
                u'issn': '0002-9483',
                u'title': u'aa',
                u'url': u'url_aa',
                u'location': 'qs',
                u'years': ['1919']},
             u'00029629sciR11A6': {
                u'building': 'foo',
                u'call_number': 'R11 .A6',
                u'issn': '0002-9629',
                u'title': u'bb',
                u'url': u'url_bb',
                u'location': 'sci',
                u'years': ['1926', '1928']},
             u'0022197XrsmchJX1C58': {
                u'building': 'foo',
                u'call_number': 'JX1 .C58',
                u'issn': '0022-197X',
                u'title': u'cc',
                u'url': u'url_cc',
                u'location': 'rsmch',
                u'years': ['1991', '1992']},
             u'00318701sciTR1P58': {
                u'building': 'foo',
                u'call_number': 'TR1 .P58',
                u'issn': '0031-8701',
                u'title': u'dd',
                u'url': u'url_dd',
                u'location': 'sci',
                u'title': u'dd',
                u'years': ['1962']},
             u'00802042qsQP1E7': {
                u'building': 'foo',
                u'call_number': 'QP1 .E7',
                u'issn': '0080-2042',
                u'title': u'ee',
                u'url': u'url_ee',
                u'location': 'qs',
                u'years': ['1937', '1938']},
             u'04927079sci1SIZETN24T2A2': {
                u'building': 'foo',
                u'call_number': '1-SIZE TN24.T2 A2',
                u'issn': '0492-7079',
                u'title': u'ff',
                u'url': u'url_ff',
                u'location': 'sci',
                u'years': ['1971']}
            }
        self.assertEqual(
            [[u'000294831919', u'0002-9483', u'aa', u'url_aa', u'qs', 'foo', u'1-SIZE GN1 .A55', 1919, 1919],
             [u'000296291926', u'0002-9629', u'bb', u'url_bb',  u'sci', 'foo', u'R11 .A6', 1926, 1926],
             [u'000296291928', u'0002-9629', u'bb', u'url_bb',  u'sci', 'foo', u'R11 .A6', 1928, 1928],
             [u'0022197X1991', u'0022-197X', u'cc', u'url_cc',  u'rsmch', 'foo', u'JX1 .C58', 1991, 1992],
             [u'003187011962', u'0031-8701', u'dd', u'url_dd',  u'sci', 'foo', u'TR1 .P58', 1962, 1962],
             [u'008020421937', u'0080-2042', u'ee', u'url_ee',  u'qs', 'foo', u'QP1 .E7', 1937, 1938],
             [u'049270791971', u'0492-7079', u'ff', u'url_ff',  u'sci', 'foo', u'1-SIZE TN24.T2 A2', 1971, 1971]],
            self.processor.build_holdings_lst( holdings_dct )
            )

    # end class RapidFileProcessorTest


class HoldingsDctBuilderTest( TestCase ):
    """ Tests models.HoldingsDctBuilder """

    def setUp( self ):
        """ Runs initialization. """
        self.builder = HoldingsDctBuilder(
            settings_app.TEST_FROM_RAPID_UTF8_FILEPATH,
            )

    def test__build_holdings_elements( self):
        """ Checkds dct-entry prepared from row data.
            Returned data definition: ( key, issn, title, location, building, callnumber, year ) """
        row = [u'RBN', u'Main Library', u'sci', u'1-SIZE TN24.T2 A2', u'Information circular / State of Tennessee Department of Conservation, Division of Geology', u'Print', u'0492-7079', u'ISSN', u'', u'', u'1971']
        self.assertEqual(
            (u'04927079Sciences1SIZETN24T2A2', u'0492-7079', u'Information circular / State of Tennessee Department of Conservation, Division of Geology', u'sci', u'Sciences', u'1-SIZE TN24.T2 A2', u'1971'),
            self.builder._build_holdings_elements(row)
            )

    def test__build_url( self ):
        """ Checks url built from title. """
        title = '5th IEEE International Workshop on Object-Orientation in Operating Systems'
        self.assertEqual(
            'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=5th+IEEE+International+Workshop+on+Object-Orientation+in+Operating+Systems',
            self.builder._build_url( title )
            )

    def test__build_url_nonascii( self ):
        """ Checks temporary handling of non-ascii text. """
        title = 'Zeitschrift für anorganische und allgemeine Chemie'
        self.assertEqual(
            'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=Zeitschrift+anorganische+und+allgemeine+Chemie',
            self.builder._build_url( title )
            )

    def test__build_holdings_dct( self ):
        """ Tests filtering and parsing of records for easyAccess db. """
        # pprint.pprint( self.builder.build_holdings_dct() )
        self.assertEqual( {
            u'00029483Annex1SIZEGN1A55': {
                u'building': u'Annex',
                u'call_number': u'1-SIZE GN1 .A55',
                u'issn': u'0002-9483',
                u'location': u'qs',
                u'title': u'American journal of physical anthropology',
                u'url': u'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=American+journal+of+physical+anthropology',
                u'years': [u'1919']},
            u'00029629SciencesR11A6': {
                u'building': u'Sciences',
                u'call_number': u'R11 .A6',
                u'issn': u'0002-9629',
                u'location': u'sci',
                u'title': u'The American journal of the medical sciences',
                u'url': u'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=The+American+journal+of+the+medical+sciences',
                u'years': [u'1926', u'1928']},
            u'0022197XRockJX1C58': {
                u'building': u'Rock',
                u'call_number': u'JX1 .C58',
                u'issn': u'0022-197X',
                u'location': u'rsmch',
                u'title': u'Journal of international affairs',
                u'url': u'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=Journal+of+international+affairs',
                u'years': [u'1991', u'1992']},
            u'00318701SciencesTR1P58': {
                u'building': u'Sciences',
                u'call_number': u'TR1 .P58',
                u'issn': u'0031-8701',
                u'location': u'sci',
                u'title': u'Photographic abstracts',
                u'url': u'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=Photographic+abstracts',
                u'years': [u'1962']},
            u'00802042AnnexQP1E7': {
                u'building': u'Annex',
                u'call_number': u'QP1 .E7',
                u'issn': u'0080-2042',
                u'location': u'qs',
                u'title': u'Ergebnisse der Physiologie biologischen Chemie und experimentellen Pharmakologie. Reviews of physiology, biochemistry, and experimental pharmacology',
                u'url': u'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=Ergebnisse+der+Physiologie+biologischen+Chemie+und+experimentellen+Pharmakologie.+Reviews+of+physiology%2C+biochemistry%2C+and+experimental+pharmacology',
                u'years': [u'1937', u'1938']},
            u'04927079Sciences1SIZETN24T2A2': {
                u'building': u'Sciences',
                u'call_number': u'1-SIZE TN24.T2 A2',
                u'issn': u'0492-7079',
                u'location': u'sci',
                u'title': u'Information circular / State of Tennessee Department of Conservation, Division of Geology',
                u'url': u'https://search.library.brown.edu/catalog/?f[format][]=Periodical%20Title&q=Information+circular+%2F+State+of+Tennessee+Department+of+Conservation%2C+Division+of+Geology',
                u'years': [u'1971']}},
            self.builder.build_holdings_dct()
            )

    # end class HoldingsDctBuilderTest


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


class SSBuilderTest( TestCase ):
    """ Tests functions for building the serials-solutions file. """

    def setUp( self ):
        self.builder = SSBuilder()

    def test__build_row( self ):
        """ Checks built row. """
        model_data = {
            'issn': '0003-4398',
            'year_start': 1999,
            'year_end': 2007,
            'building': 'Rock',
            'callnumber': 'DC607.1 .A6',
            'title': "Annales du Midi; revue archéologique, historique, et philologique de la France méridionale; sous les auspices de l'Université de Toulouse",
            'url': 'https://search.library.brown.edu/catalog/?q=Annales+du+Midi+revue&f%5Bformat%5D%5B%5D=Periodical+Title'
            }
        result = self.builder.build_row( model_data )
        self.assertEqual( {
            'issn': '0003-4398',
            'title': "Annales du Midi; revue archéologique, historique, et philologique de la France méridionale; sous les auspices de l'Université de Toulouse",
            'type': 'Journal',
            'url': 'https://search.library.brown.edu/catalog/?q=Annales+du+Midi+revue&f%5Bformat%5D%5B%5D=Periodical+Title',
            'location': 'Rock - DC607.1 .A6',
            'display_location_note': 'Yes',
            'year_start': '1999',
            'year_end': '2007',
            },
            self.builder.row_dct
            )
        self.assertEqual(
            [
            '0003-4398',
            "Annales du Midi; revue archéologique, historique, et philologique de la France méridionale; sous les auspices de l'Université de Toulouse",
            'bar' ],
            self.builder.build_row( model_data )
            )


class SqlAlchemyTest( TestCase ):
    """ Mostly serves as documentation for how to use sqlalchemy to execute basic sql. """

    def setUp( self ):
        """ Makes sure no `dummy_test_table` exists, then creates it. """
        log.debug( 'running setUp' )
        self.db_session = None
        self._setup_db_session()
        self._ensure_no_test_table()
        self._create_test_table()
        self._ensure_test_table()

    def _setup_db_session( self ):
        """ Initializes db_session.
            Called by setUp() """
        engine = alchemy_create_engine( settings_app.TEST_DB_CONNECTION_URL )
        Session = alchemy_scoped_session( alchemy_sessionmaker(bind=engine) )
        db_session = Session()
        self.db_session = db_session
        return

    def _ensure_no_test_table( self ):
        """ Runs select which will fail, expectedly, if test-table does not exist.
            Called by setUp() """
        try:
            result = self.db_session.execute( 'SELECT * FROM `dummy_test_table`' )
            raise Exception( 'EXCEPTION: dummy_test_table found on test-initialization' )
        except Exception as e:
            pass
        return

    def _create_test_table( self ):
        """ Creates test-table with two records
            Called by setUp() """
        sql_a = '''
            CREATE TABLE `dummy_test_table` (
            `key` varchar( 20 ) NOT NULL ,
            `issn` varchar( 15 ) NOT NULL ,
            `start` int( 11 )  NOT NULL ,
            `end` int( 11 )  DEFAULT NULL ,
            `location` varchar( 25 ) DEFAULT NULL ,
            `call_number` varchar( 50 ) DEFAULT NULL ,
            PRIMARY KEY (`key`)
            );
            '''
        sql_b = '''
            INSERT INTO `dummy_test_table`
            (`key`, `issn`, `start`, `end`, `location`, `call_number`)
            VALUES
            ('the key', 'the issn', 1980, 1982, 'the location', 'the callnumber');
            '''
        result = self.db_session.execute( sql_a )
        result = self.db_session.execute( sql_b )
        resultset_lst = []
        return

    def _ensure_test_table( self ):
        """ Checks that `dummy_test_backup_table` has been created. """
        flag = 'init'
        sql = '''SELECT * FROM `dummy_test_table`;'''
        resultset = self.db_session.execute( sql )
        lst = []
        for row in resultset:
            lst.append( row )
        # pprint.pprint( lst )
        self.assertEqual(
            [(u'the key', u'the issn', 1980, 1982, u'the location', u'the callnumber')],
            lst
            )

    ## actual tests ##

    def test__something( self ):
        """ Without this the setup and teardown real test work won't occur.
            Can use this to eventually perhaps test the real make_backup() function. """
        self.assertEqual( 2, 2 )

    ## end actual tests ##

    def tearDown( self ):
        """ Deletes `dummy_test_table` and `dummy_test_backup_table` """
        log.debug( 'running tearDown' )
        sql = '''DROP TABLE  `dummy_test_table`;'''
        try:
            result = self.db_session.execute( sql )
        except Exception as e:
            raise Exception( '%s' % unicode(repr(e)) )
        finally:
            self.db_session.close()
        return

    # end class SqlAlchemyTest


# class RapidFileGrabberTest( TestCase ):
#     """ Tests models.RapidFileGrabber() """

#     def setUp( self ):
#         """ Runs initialization; ensures test-file doesn't exist locally. """
#         assert os.path.isfile( settings_app.TEST_LOCAL_DESTINATION_FILEPATH ) == False
#         self.grabber = RapidFileGrabber(
#             settings_app.TEST_REMOTE_SERVER_NAME,
#             settings_app.TEST_REMOTE_SERVER_PORT,
#             settings_app.TEST_REMOTE_SERVER_USERNAME,
#             settings_app.TEST_REMOTE_SERVER_PASSWORD,
#             settings_app.TEST_REMOTE_FILEPATH,
#             settings_app.TEST_LOCAL_DESTINATION_FILEPATH,
#             settings_app.TEST_ZIPFILE_EXTRACT_DIR_PATH,
#             )

#     def test__grab_file( self ):
#         """ Tests grab of remote file. """
#         self.grabber.grab_file()
#         self.assertEqual(
#             2277,  # bytes
#             os.path.getsize(settings_app.TEST_LOCAL_DESTINATION_FILEPATH) )

#     def test__unzip_file( self ):
#         """ Tests unzip of downloaded file. """
#         self.grabber.local_destination_filepath = settings_app.TEST_ZIPFILE_FILEPATH  # rapid_app/test_files/test_RBNextract.zip
#         self.grabber.unzip_file()
#         self.assertEqual(
#             20576,  # bytes
#             os.path.getsize('%s/%s' % (settings_app.TEST_ZIPFILE_EXTRACT_DIR_PATH, settings_app.TEST_ZIPFILE_EXTRACT_FILENAME)) )

#     def tearDown( self ):
#         """ Removes downloaded test-file. """
#         if os.path.isfile( settings_app.TEST_LOCAL_DESTINATION_FILEPATH ):
#             os.remove( settings_app.TEST_LOCAL_DESTINATION_FILEPATH )

#     # end class RapidFileGrabberTest
