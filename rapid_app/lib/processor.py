# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, itertools, logging, operator, pprint
from rapid_app.models import HoldingsDctBuilder, Utf8Maker  # TODO: move out of models.py
from rapid_app.models import PrintTitleDev

log = logging.getLogger(__name__)


class RapidFileProcessor( object ):
    """ Handles processing of file from Rapid.
        Main worker function: parse_file_from_rapid() """

    def __init__(self, from_rapid_filepath, from_rapid_utf8_filepath ):
        # self.from_rapid_filepath = from_rapid_filepath  # actual initial file from rapid
        log.debug( 'initialized source-path, ```{source}```; destination-utf8-path, ```{destination}```'.format(source=from_rapid_filepath, destination=from_rapid_utf8_filepath) )
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath
        self.holdings_defs_dct = {
            'key': 0, 'issn': 1, 'location': 2, 'building': 3, 'callnumber': 4, 'year_start': 5, 'year_end': 6 }
        self.utf8_maker = Utf8Maker( from_rapid_filepath, from_rapid_utf8_filepath )

    def parse_file_from_rapid( self ):
        """ Extracts print holdings from the file-from-rapid.
            That file contains both print and online holdings.
            Steps...
              - a file is created that is known to be utf8-good
              - to continue...
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
        for ( key, val ) in holdings_dct.items():
            year_lst = val['years']
            log.debug( 'year_lst, `%s`' % year_lst )
            holdings_dct[key]['years_contig'] = self._contigify_list( year_lst )
            holdings_dct[key]['years_held'] = self._build_years_held( holdings_dct[key]['years_contig'] )
            holdings_lst = self._update_holdings_lst( holdings_lst, val )
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
        issn = issn_dct['issn']
        location = issn_dct['location']
        building = issn_dct['building']
        callnumber = issn_dct['call_number']
        for period_dct in issn_dct['years_held']:
            new_key = '%s%s' % ( issn.replace('-', ''), period_dct['start'] )
            update_lst = [ new_key, issn, location, building, callnumber, period_dct['start'], period_dct['end'] ]
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
            title = PrintTitleDev()
            title.key = row[self.holdings_defs_dct['key']]
            title.issn = row[self.holdings_defs_dct['issn']]
            title.start = row[self.holdings_defs_dct['year_start']]
            title.end = row[self.holdings_defs_dct['year_end']]
            title.location = row[self.holdings_defs_dct['location']]
            title.building = row[self.holdings_defs_dct['building']]
            title.call_number = row[self.holdings_defs_dct['callnumber']]
            title.updated = unicode( datetime.date.today() )
            title.save()
        return

    def _run_dev_db_deletes( self, holdings_lst ):
        """ Removes outdated dev-db title entries.
            Called by update_dev_db() """
        key_list = []
        for row in holdings_lst:
            holdings_key = row[self.holdings_defs_dct['key']]
            if holdings_key not in key_list:
                key_list.append( holdings_key )
        titles = PrintTitleDev.objects.all()
        for title in titles:
            if title.key not in key_list:
                title.delete()
        return

    # end class RapidFileProcessor
