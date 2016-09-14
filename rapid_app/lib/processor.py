# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs, csv, datetime, itertools, json, logging, operator, pprint, shutil, urllib
import requests
from django.utils.http import urlquote_plus
from rapid_app import settings_app
from rapid_app.models import PrintTitleDev, ProcessorTracker

log = logging.getLogger(__name__)


class RapidFileProcessor( object ):
    """ Handles processing of file from Rapid.
        Main worker function: parse_file_from_rapid() """

    def __init__(self, from_rapid_filepath, from_rapid_utf8_filepath ):
        log.debug( 'initialized source-path, ```{source}```; destination-utf8-path, ```{destination}```'.format(source=from_rapid_filepath, destination=from_rapid_utf8_filepath) )
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath
        self.updated_holdings_defs_dct = {
            'key': 0, 'issn': 1, 'title': 2, 'url': 3, 'location': 4, 'building': 5, 'callnumber': 6, 'year_start': 7, 'year_end': 8 }
        self.utf8_maker = Utf8Maker( from_rapid_filepath, from_rapid_utf8_filepath )

    def parse_file_from_rapid( self ):
        """ Extracts print holdings from the file-from-rapid.
            That file contains both print and online holdings.
            Steps...
              - a file from-rapid is created that is known to be utf8-good
              - iterates through that file looking for `Print` entries; for those entries...  # HoldingsDctBuilder.build_holdings_dct()
                - valid and massaged row-elements are obtained (sometimes a title contains unescaped commas)...  # HoldingsDctBuilder.process_file_row()
                - if the entry doesn't exist, it's added to a holdings-dct (unique key on modified-issn & location & modified-callnumber)
              - a list is created from the dct of all print holdings, primarily making year-ranges  # build_holdings_lst()
              - the preview-db is updated  # update_dev_db()
              - the list is returned to the view in case the user requests a json response; othewise, the response is the preview admin screen.
            Called by viewhelper_processfile.ProcessFileFromRapidHelper.initiate_work() """
        log.debug( 'starting parse' )
        if self.utf8_maker.check_utf8() is False:
            self.utf8_maker.make_utf8()
        else:
            self.utf8_maker.copy_utf8()
        holdings_dct_builder = HoldingsDctBuilder( self.from_rapid_utf8_filepath )
        holdings_dct = holdings_dct_builder.build_holdings_dct()
        holdings_lst = self.build_holdings_lst( holdings_dct )
        self.update_dev_db( holdings_lst )
        return holdings_lst

    def build_holdings_lst( self, holdings_dct ):
        """ Converts the holdings_dct into a list of entries ready for db update.
            Main work is taking the multiple year entries and making ranges.
            Called by parse_file_from_rapid() """
        holdings_lst = []
        for ( key, dct_val ) in holdings_dct.items():
            year_lst = dct_val['years']
            log.debug( 'year_lst, `%s`' % year_lst )
            holdings_dct[key]['years_contig'] = self._contigify_list( year_lst )
            holdings_dct[key]['years_held'] = self._build_years_held( holdings_dct[key]['years_contig'] )
            holdings_lst = self._update_holdings_lst( holdings_lst, dct_val )
        sorted_lst = sorted( holdings_lst )
        log.info( 'holdings_lst, ```%s```' % pprint.pformat(sorted_lst) )
        return sorted_lst

    def _contigify_list( self, lst ):
        """ Converts sorted list entries into sub-lists that are contiguous.
            Eg: [ 1, 2, 4, 5 ] -> [ [1, 2], [4, 5] ]
            Credit: <http://stackoverflow.com/questions/3149440/python-splitting-list-based-on-missing-numbers-in-a-sequence>
            Called by build_holdings_list() """
        contig_lst = []
        if lst == ['']:
            return contig_lst
        int_lst = [ int(x) for x in lst ]
        for k, g in itertools.groupby( enumerate(int_lst), lambda (i,x):i-x ):
            contig_lst.append( map(operator.itemgetter(1), g) )
        log.debug( 'contig_lst, `%s`' % contig_lst )
        return contig_lst

    def _build_years_held( self, contig_lst ):
        """ Converts contig_list to list of [ {'start': year-a, 'end': 'year-b'}, {'start': year-c, 'end': 'year-d'} ] entries.
            Called by build_holdings_list() """
        years_held_lst = []
        for lst in contig_lst:
            for year in lst:
                start = lst[0]
                end = lst[-1]
                # end = lst[-1] if lst[-1] is not start else ( lst[-1] + 1 )
                start_end_dct = {'start': start, 'end':end}
                if start_end_dct not in years_held_lst:
                    years_held_lst.append( start_end_dct )
        log.debug( 'years_held_lst, `%s`' % years_held_lst )
        return years_held_lst

    def _update_holdings_lst( self, holdings_lst, issn_dct ):
        """ Builds final data lst entry.
            Called by build_holdings_lst() """
        ( issn, location, building ) = ( issn_dct['issn'], issn_dct['location'], issn_dct['building'] )
        ( callnumber, title, url ) = ( issn_dct['call_number'], issn_dct['title'], issn_dct['url'] )
        for period_dct in issn_dct['years_held']:
            new_key = '%s%s' % ( issn.replace('-', ''), period_dct['start'] )
            update_lst = [ new_key, issn, title, url, location, building, callnumber, period_dct['start'], period_dct['end'] ]
            log.debug( 'update_lst, `%s`' % update_lst )
            if update_lst not in holdings_lst:
                log.debug( 'gonna update' )
                holdings_lst.append( update_lst )
        return holdings_lst

    def update_dev_db( self, holdings_lst ):
        """ Adds and removes dev-db title entries.
            Called by parse_file_from_rapid() """
        self._run_dev_db_adds( holdings_lst )
        self._run_dev_db_deletes( holdings_lst )
        return

    def _run_dev_db_adds( self, holdings_lst ):
        """ Populates a db table that can be viewed before replacing the production db table.
            Assumes an index on unique `key` field.
            Called by update_dev_db() """
        for row in holdings_lst:
            log.debug( 'row, ```{}```'.format(pprint.pformat(row)) )
            title = PrintTitleDev()
            title.key = row[self.updated_holdings_defs_dct['key']]
            title.issn = row[self.updated_holdings_defs_dct['issn']]
            title.title = row[self.updated_holdings_defs_dct['title']]
            title.url = row[self.updated_holdings_defs_dct['url']]
            title.start = row[self.updated_holdings_defs_dct['year_start']]
            title.end = row[self.updated_holdings_defs_dct['year_end']]
            title.location = row[self.updated_holdings_defs_dct['location']]
            title.building = row[self.updated_holdings_defs_dct['building']]
            title.call_number = row[self.updated_holdings_defs_dct['callnumber']]
            title.updated = unicode( datetime.date.today() )
            title.save()
        return

    def _run_dev_db_deletes( self, holdings_lst ):
        """ Removes outdated dev-db title entries.
            Called by update_dev_db() """
        key_list = []
        for row in holdings_lst:
            holdings_key = row[self.updated_holdings_defs_dct['key']]
            if holdings_key not in key_list:
                key_list.append( holdings_key )
        titles = PrintTitleDev.objects.all()
        for title in titles:
            if title.key not in key_list:
                title.delete()
        return

    # end class RapidFileProcessor


class Utf8Maker( object ):
    """ Ensures file contains utf-8 data.
        Non-django class. """

    def __init__(self, from_rapid_filepath, from_rapid_utf8_filepath ):
        self.from_rapid_filepath = from_rapid_filepath  # actual initial file from rapid
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath

    def check_utf8( self, filepath=None ):
        """ Ensures file is utf-8 readable.
            Will error and return False if not.
            Called by parse_file_from_rapid() """
        path = filepath if filepath else self.from_rapid_filepath
        log.debug( 'checked path, `%s`' % path )
        utf8 = False
        with codecs.open( path, 'rb', 'utf-8' ) as myfile:
            try:
                for line in myfile:  # reads line-by-line; doesn't tax memory on big files
                    pass
                utf8 = True
            except Exception as e:
                log.error( 'EXPECTED exception, `%s`' % unicode(repr(e)) )
        log.debug( 'utf8 check, `{}`'.format(utf8) )
        return utf8

    def make_utf8( self ):
        """ Iterates through each line; ensures it can be converted to utf-8.
            Called by parse_file_from_rapid() """
        try:
            log.debug( 'src-path, `%s`; dest-path, `%s`' % (self.from_rapid_filepath, self.from_rapid_utf8_filepath) )
            with codecs.open( self.from_rapid_filepath, 'rb', 'utf-16' ) as input_file:
                with open( self.from_rapid_utf8_filepath, 'wb' ) as output_file:
                    self._run_utf8_write( input_file, output_file )
            log.debug( 'utf8 file now at, `%s`' % self.from_rapid_utf8_filepath )
        except Exception as e:
            log.error( 'exception on source or destination file, `%s`' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )
        return

    def _run_utf8_write( self, input_file, output_file ):
        """ Runs the line-by-line utf8 transform.
            Called by make_utf8() """
        for line in input_file:
            try:
                # assert( type(line) == unicode )
                output_file.write( line.encode('utf-8') )
            except Exception as e:
                log.error( 'exception, `%s`' % unicode(repr(e)) )
                raise Exception( unicode(repr(e)) )
        return

    def copy_utf8( self ):
        """ Copies good utf8 source file to utf8-filepath.
            Called by parse_file_from_rapid() """
        shutil.copy2( self.from_rapid_filepath, self.from_rapid_utf8_filepath )
        return

    # end class Utf8Maker


class HoldingsDctBuilder( object ):
    """ Builds dct of holdings from file.
        Non-django class. """

    def __init__(self, from_rapid_utf8_filepath ):
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath
        self.defs_dct = {  # proper row field-definitions
            'library': 0,
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
        self.row_fixer = RowFixer( self.defs_dct )
        self.locations_dct = self.update_locations_dct()
        self.tracker_updater = TrackerUpdater()
        self.title_maker = TitleMaker()

    def update_locations_dct( self ):
        """ Populates class attribute with locations dct, used to populate `building` field.
            Called by __init__() """
        r = requests.get( settings_app.LOCATIONS_URL )
        dct = r.json()
        return dct

    def build_holdings_dct( self ):
        """ Iterates through file, grabbing normalized print holdings.
            Sample print entries:
                `RBN,Main Library,sci,TR1 .P58,Photographic abstracts,Print,0031-8701,ISSN,,,1962`
                `RBN,Main Library,qs,QP1 .E7,Ergebnisse der Physiologie, biologischen Chemie und experimentellen Pharmakologie...,Print,0080-2042,ISSN,1,69,1938`
            Note: there are unescaped commas in some of the titles. Grrr.
            Builds and returns a dict like {
                u'00029629sciR11A6': {
                    u'call_number': 'R11 .A6',
                    u'issn': '0002-9629',
                    u'location': 'sci',
                    u'years': ['1926', '1928'] },  # years are sorted
                u'abc123': {
                    ... },
                    }
            Called by RapidFileProcessor.parse_file_from_rapid() """
        log.debug( 'starting build_holdings_dct()' )
        ( holdings_dct, csv_ref, entries_count ) = self.prep_holdings_dct_processing()
        for (idx, row) in enumerate(csv_ref):  # row is type() `list`
            self.track_row( idx, entries_count )
            if 'Print' not in row:
                continue
            ( key, issn, title, location, building, callnumber, year ) = self.process_file_row( row )
            holdings_dct = self.update_holdings_dct( holdings_dct, key, issn, title, location, building, callnumber, year )
        log.info( 'holdings_dct, ```%s```' % pprint.pformat(holdings_dct) )
        log.debug( 'TEMP; issn-title dct, ```{}```'.format(self.title_maker.good_titles_dct) )
        return holdings_dct

    def prep_holdings_dct_processing( self ):
        """ Sets initial vars.
            Called by build_holdings_dct() """
        log.debug( 'using utf8-filepath, ```{}```'.format(self.from_rapid_utf8_filepath) )
        holdings_dct = {}
        tmp_csv_ref = csv.reader( open(self.from_rapid_utf8_filepath), dialect=csv.excel, delimiter=','.encode('utf-8') )
        entries_count = sum( 1 for row in tmp_csv_ref )  # runs through file, so have to open again
        csv_ref = csv.reader( open(self.from_rapid_utf8_filepath), dialect=csv.excel, delimiter=','.encode('utf-8') )
        log.debug( 'entries_count, `%s`' % entries_count )
        return ( holdings_dct, csv_ref, entries_count )

    def track_row( self, row_idx, entries_count ):
        """ Logs progress and updates status-db.
            Called by build_holdings_dct() """
        tn_prcnt = int( entries_count * .1 )  # ten percent
        if row_idx % tn_prcnt == 0:  # uses modulo
            prcnt_done = row_idx / (tn_prcnt/10)
            log.info( '%s percent done (on row %s of %s)' % (prcnt_done, row_idx+1, entries_count) )  # +1 for 0 index
            self.tracker_updater.update_db_tracker( prcnt_done, entries_count )
        elif row_idx == 0:
            self.tracker_updater.update_db_tracker( 0, entries_count )
        elif row_idx + 1 == entries_count:
            self.tracker_updater.update_db_tracker( 100, entries_count )
        return

    def process_file_row( self, row ):
        """ Fixes row if necessary and builds elements.
            Called by build_holdings_dct() """
        row = [ field.decode('utf-8') for field in row ]
        if len( row ) > 11:  # titles with commas
            row = self.row_fixer.fix_row( row )
        ( key, issn, title, location, building, callnumber, year ) = self._build_holdings_elements( row )
        return ( key, issn, title, location, building, callnumber, year )

    def _build_holdings_elements( self, row ):
        """ Extracts data from row-list.
            Called by _process_file_row() """
        callnumber = row[self.defs_dct['callnumber']]
        issn = row[self.defs_dct['issn_num']]
        # title = self._make_title( issn, row[self.defs_dct['title']] )
        title = self.title_maker.build_title( issn, row[self.defs_dct['title']] )
        location = row[self.defs_dct['location']]
        building = self._make_building( location )
        year = row[self.defs_dct['year']]
        normalized_issn = issn.replace( '-', '' )
        normalized_callnumber = callnumber.replace( '-', '' ).replace( ' ', '' ).replace( '.', '' )
        key = '%s%s%s' % ( normalized_issn, building, normalized_callnumber  )
        return ( key, issn, title, location, building, callnumber, year )

    def _make_building( self, location ):
        """ Adds building-location.
            Called by _build_holdings_elements() """
        building = None
        try:
            building = self.locations_dct['result']['items'][location]['building']
        except KeyError:
            if location.startswith('r'):
                building = 'Rock'
            elif location.startswith('h'):
                building = 'Hay'
            elif location.startswith('q'):
                building = 'Annex'
            else:
                log.warning( 'location code {} not recognized'.format(location) )
                building = location
        return building

    def update_holdings_dct( self, holdings, key, issn, title, location, building, callnumber, year ):
        """ Updates holdings dct.
            Called by: build_holdings_dct() """
        if key not in holdings.keys():
            holdings[key] = {
                'issn': issn, 'title': title, 'url': self._build_url(title), 'location': location, 'building': building, 'call_number': callnumber, 'years': [year] }
        else:
            if year and year not in holdings[key]['years']:
                holdings[key]['years'].append( year )
                holdings[key]['years'].sort()
        # log.debug( 'holdings, ```%s```' % pprint.pformat(holdings) )
        return holdings

    def _build_url( self, title ):
        """ Builds search-url.
            Eventually should be able to use good url as-is -- this works around current encoding issue.
                Testing shows that an incorrectly encoded search will not return results, but eliminating the problemmatic world will. """
        new_word_list = []
        for word in title.split():
            try:
                word.encode( 'ascii' )
                new_word_list.append( word )
            except:
                pass
        search_title = ' '.join( new_word_list )
        params = { 'f[format][]': 'Periodical Title', 'q': search_title }
        url = 'https://search.library.brown.edu/catalog/?{}'.format( urllib.urlencode(params) )
        return url

    # end class HoldingsDctBuilder


class TitleMaker( object ):
    """ Tries to reliably get a unicode-friendly title from issn.
        Main controller: build_title() """

    def __init__( self ):
        self.good_titles_dct = {}  # populated by build_title()

    def build_title( self, issn, title ):
        """ Checks issn against built-dct or hits blacklight-solr.
            Called by HoldingsDctBuilder._build_holdings_elements() """
        if self.is_ascii( title ):
            return title
        ( found_title, dct_check ) = self.check_dct( issn )
        if dct_check:
            return found_title
        ( found_title, solr_check ) = self.check_solr( issn )
        if solr_check:
            return found_title
        log.debug( 'returning original title' )
        return title

    def is_ascii( self, title ):
        """ Yup; checks ascii.
            Called by build_title() """
        try:
            title.encode( 'ascii' )
            log.debug( 'skipping plain title' )
            return title
        except Exception as e:
            return None

    def check_dct( self, issn ):
        """ Sees if a match has already been found.
            Called by build_title() """
        ( title, dct_check ) = ( None, False )
        if issn in self.good_titles_dct.keys():
            title = self.good_titles_dct[ issn ]
            dct_check = True
            log.debug( 'found in dct' )
        return ( title, dct_check )

    def check_solr( self, issn ):
        """ Looks up issn in discovery-solr.
            Called by build_title() """
        params = { 'wt': 'json', 'indent': 'on', 'fq': 'issn_t:"{}"'.format( issn ) }
        r = requests.get( settings_app.DISCOVERY_SOLR_URL, params=params )
        log.debug( 'url, ```{}```'.format(r.url) )
        dct = r.json()
        ( title, solr_check ) = self._parse_solr( dct )
        return ( title, solr_check )

    def _parse_solr( self, dct ):
        """ Parses issn-query response.
            Called by check_solr() """
        ( title, solr_check ) = ( None, False )
        if dct['response']['numFound'] > 1:
            log.debug( 'multiples found, ```{}```'.format(pprint.pformat(dct)) )
        try:
            title = dct['response']['docs'][0]['title_display']
            solr_check = True
            log.debug( 'returning title, ```{}```'.format(title) )
        except Exception as e:
            log.debug( 'no `title_display` found' )
        return ( title, solr_check )

    # end class TitleMaker


class TrackerUpdater( object ):
    """ Manages updating of ProcessorTracker table.
        Main controller: update_db_tracker() """

    def update_db_tracker( self, prcnt_done, entries_count ):
        """ Updates db processing tracker.
            Called by track_row() """
        tracker = ProcessorTracker.objects.all()[0]
        recent_processing_dct = json.loads( tracker.recent_processing ); log.debug( 'recent_processing_dct initially, ```{}```'.format(pprint.pformat(recent_processing_dct)) )
        ( start_timestamp, end_timestamp, recent_times_per_record, average_time_per_record ) = (
            tracker.processing_started, tracker.processing_ended, recent_processing_dct['recent_times_per_record'] , recent_processing_dct['average_time_per_record'] )  # existing info
        ( status, records_left, start_timestamp, end_timestamp, recent_times_per_record, average_time_per_record ) = self._check_percent_done(
            prcnt_done, entries_count, start_timestamp, end_timestamp, recent_times_per_record, average_time_per_record )  # updated info
        time_left = ( records_left * average_time_per_record ) / 60  # seconds-left / 60
        recent_processing_jsn = self._update_recent_processing(
            recent_processing_dct, prcnt_done, recent_times_per_record, time_left, average_time_per_record )
        self._update_tracker_object( tracker, recent_processing_jsn, status, start_timestamp, end_timestamp )
        return

    def _check_percent_done( self, prcnt_done, entries_count, start_timestamp, end_timestamp, recent_times_per_record, average_time_per_record ):
        """ Updates vars based on percent done.
            Called by update_db_tracker() """
        if prcnt_done == 0:
            ( status, start_timestamp, records_left ) = ( 'started', datetime.datetime.now(), entries_count )
        elif prcnt_done == 100:
            ( status, end_timestamp, records_left ) = ( 'complete', datetime.datetime.now(), 0 )
            recent_times_per_record = self._update_recent_times_per_record( recent_times_per_record, start_timestamp, end_timestamp, entries_count )
            average_time_per_record = sum(recent_times_per_record) / float( len(recent_times_per_record) )
        else:
            ( status, records_done ) = ( 'in_process', (entries_count * (prcnt_done/100.0)) )
            records_left = entries_count - records_done
        return ( status, records_left, start_timestamp, end_timestamp, recent_times_per_record, average_time_per_record )

    def _update_recent_times_per_record( self, recent_times_per_record, start_timestamp, end_timestamp, entries_count ):
        """ Updates list of recent-times-per-record (seconds).
            Called by: _check_percent_done() """
        time_taken = end_timestamp - start_timestamp
        time_taken_string = '{sec}.{microsec}'.format( sec=time_taken.seconds, microsec=time_taken.microseconds )
        f = float( time_taken_string )
        time_per_record = f / entries_count
        recent_times_per_record.append( time_per_record )
        recent_times_per_record = recent_times_per_record [0:4]
        log.debug( 'recent_times_per_record, ```{}```'.format(recent_times_per_record) )
        return recent_times_per_record

    def _update_recent_processing( self, recent_processing_dct, prcnt_done, recent_times_per_record, time_left, average_time_per_record ):
        """ Updates recent_processing_dct and returns json.
            Called by update_db_tracker() """
        recent_processing_dct['percent_done'] = prcnt_done
        recent_processing_dct['recent_times_per_record'] = recent_times_per_record
        recent_processing_dct['time_left'] = time_left
        recent_processing_dct['average_time_per_record'] = average_time_per_record
        log.debug( 'recent_processing_dct after update, ```{}```'.format(pprint.pformat(recent_processing_dct)) )
        jsn = json.dumps( recent_processing_dct )
        return jsn

    def _update_tracker_object( self, tracker, recent_processing_jsn, status, start_timestamp, end_timestamp ):
        """ Updates and saves tracker record.
            Called by update_db_tracker() """
        tracker.recent_processing = recent_processing_jsn
        tracker.current_status = status
        tracker.processing_started = start_timestamp
        tracker.processing_ended = end_timestamp
        tracker.save()
        log.debug( 'tracker updated' )
        return

    # end class TrackerUpdater()


class RowFixer( object ):
    """ Fixes non-escaped csv strings.
        Non-django class. """

    def __init__(self, defs_dct ):
        self.defs_dct = defs_dct  # { 'label 1': 'index position 1', ... }

    def fix_row( self, row ):
        """ Handles row containing non-escaped commas in title.
            Called by RapidFileProcessor.build_holdings_dct() """
        fixed_row = self.initialize_fixed_row( row )
        for field in row:
            current_element_num = row.index(field)
            fixed_row = self.update_title( fixed_row, row, current_element_num, field )
            if row[current_element_num + 1] == 'Print':
                problem_defs_dct = self.make_problem_defs_dct( current_element_num )
                fixed_row = self.finish_fixed_row( fixed_row, row, problem_defs_dct )
                break
        log.debug( 'fixed_row finally, ```%s```' % fixed_row )
        return fixed_row

    def initialize_fixed_row( self, row ):
        """ Initializes fixed row with known correct row data.
            Called by fix_row() """
        fixed_row = []
        fixed_row.append( row[self.defs_dct['library']] )
        fixed_row.append( row[self.defs_dct['branch']] )
        fixed_row.append( row[self.defs_dct['location']] )
        fixed_row.append( row[self.defs_dct['callnumber']] )
        fixed_row.append( row[self.defs_dct['title']] )
        # log.debug( 'fixed_row initially, ```%s```' % fixed_row )
        return fixed_row

    def update_title( self, fixed_row, row, current_element_num, field ):
        """ Processes additional title fields.
            Called by fix_row() """
        main_title_element_num = row.index( row[self.defs_dct['title']] )
        if current_element_num > main_title_element_num:
            if field[0:1] == ' ':  # additional title fields start with space
                fixed_row[self.defs_dct['title']] = fixed_row[self.defs_dct['title']] + field + ','
        # log.debug( 'fixed_row title updated, ```%s```' % fixed_row )
        return fixed_row

    def make_problem_defs_dct( self, current_element_num ):
        """ Creates remaining definition-dct elements, given known current_element_num.
            Called by fix_row() """
        problem_defs_dct = {
            'format': current_element_num + 1,
            'issn_num': current_element_num + 2,
            'issn_type': current_element_num + 3,
            'vol_start': current_element_num + 4,
            'vol_end': current_element_num + 5,
            'year': current_element_num + 6
            }
        log.debug( 'problem_defs_dct, ```%s```' % problem_defs_dct )
        return problem_defs_dct

    def finish_fixed_row( self, fixed_row, row, problem_defs_dct ):
        """ Updates remaining fixed-row elements.
            Called by fix_row() """
        fixed_row[self.defs_dct['title']] = fixed_row[self.defs_dct['title']][0:-1]  # slice off that last comma
        fixed_row.append( row[problem_defs_dct['format']] )
        fixed_row.append( row[problem_defs_dct['issn_num']] )
        fixed_row.append( row[problem_defs_dct['issn_type']] )
        fixed_row.append( row[problem_defs_dct['vol_start']] )
        fixed_row.append( row[problem_defs_dct['vol_end']] )
        fixed_row.append( row[problem_defs_dct['year']] )
        # log.debug( 'fixed_row finished, ```%s```' % fixed_row )
        return fixed_row

    # end class RowFixer
