# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, os, sets
from rapid_app import settings_app
from rapid_app.models import ManualDbHandler, PrintTitleDev

log = logging.getLogger(__name__)


class UpdateTitlesHelper( object ):
    """ Manages views.update_production_easyA_titles() work. """

    def __init__(self):
        self.db_handler = ManualDbHandler()

    def run_update( self, request ):
        """ Calls the backup and update code.
            Called by views.update_production_easyA_titles() """
        log.debug( 'calling update_older_backup()' )
        self.update_older_backup()
        log.debug( 'calling update_backup()' )
        self.update_backup()
        log.debug( 'calling update_production_table()' )
        self.update_production_table()
        return

    def update_older_backup( self ):
        """ Copies data from backup table to older backup table.
            Called by run_update() """
        result = self.db_handler.run_sql( sql=unicode(os.environ['RAPID__BACKUP_COUNT_SQL']), connection_url=settings_app.DB_CONNECTION_URL )
        if result[0][0] > 10000:  # result is like `[(27010,)]`; don't backup if the count is way off
            self.db_handler.run_sql(
                sql=unicode(os.environ['RAPID__BACKUP_OLDER_DELETE_SQL']), connection_url=settings_app.DB_CONNECTION_URL )
            if 'sqlite' in settings_app.DB_CONNECTION_URL:
                self.db_handler.run_sql( sql='VACUUM;', connection_url=settings_app.DB_CONNECTION_URL  )
            self.db_handler.run_sql(
                sql=unicode(os.environ['RAPID__BACKUP_OLDER_INSERT_SQL']), connection_url=settings_app.DB_CONNECTION_URL )
        else:
            log.info( 'not backing up because count is only, ```{}```'.format(result) )
        return

    def update_backup( self ):
        """ Copies data from production table to backup table.
            Called by run_update() """
        result = self.db_handler.run_sql( sql=unicode(os.environ['RAPID__PRODUCTION_COUNT_SQL']), connection_url=settings_app.DB_CONNECTION_URL )
        if result[0][0] > 10000:  # result is like `[(27010,)]`; don't backup if the count is way off
            self.db_handler.run_sql(
                sql=unicode(os.environ['RAPID__BACKUP_DELETE_SQL']), connection_url=settings_app.DB_CONNECTION_URL )
            if 'sqlite' in settings_app.DB_CONNECTION_URL:
                self.db_handler.run_sql( sql='VACUUM;', connection_url=settings_app.DB_CONNECTION_URL  )
            self.db_handler.run_sql(
                sql=unicode(os.environ['RAPID__BACKUP_INSERT_SQL']), connection_url=settings_app.DB_CONNECTION_URL )
        else:
            log.info( 'not backing up because count is only, ```{}```'.format(result) )
        return

    def update_production_table( self ):
        """ Runs update-production sql.
            Called by run_update() """
        ( rapid_keys, easya_keys, key_int ) = self._setup_vars()        # setup
        rapid_keys = self._populate_rapid_keys( rapid_keys )            # get rapid keys
        easya_keys = self._populate_easya_keys( easya_keys, key_int )   # get easyA keys
        ( rapid_not_in_easya, easya_not_in_rapid ) = self._intersect_keys( rapid_keys, easya_keys)  # intersect sets
        self._add_rapid_entries( rapid_not_in_easya )                   # insert new rapid records
        self._remove_easya_entries( easya_not_in_rapid )                # run easyA deletions
        return

    def _setup_vars( self ):
        """ Preps vars.
            Called by update_production_table() """
        rapid_keys = []
        easya_keys = []
        tuple_keys = { 'key': 0, 'issn': 1, 'start': 2, 'end': 3, 'location': 4, 'call_number': 5 }
        key_int = tuple_keys['key']  # only using zero now, might use other tuple-elements later
        return ( rapid_keys, easya_keys, key_int )

    def _populate_rapid_keys( self, rapid_keys ):
        """ Preps list of rapid keys.
            Called by update_production_table() """
        for title in PrintTitleDev.objects.all():
            rapid_keys.append( title.key )
        log.debug( 'len rapid_keys, {}'.format(len(rapid_keys)) )
        return rapid_keys

    def _populate_easya_keys( self, easya_keys, key_int ):
        """ Preps list of easya keys.
            Called by update_production_table() """
        sql = 'SELECT * FROM `{}`'.format( unicode(os.environ['RAPID__TITLES_TABLE_NAME']) )
        result = self.db_handler.run_sql( sql=sql, connection_url=settings_app.DB_CONNECTION_URL )
        for row_tuple in result:
            easya_keys.append( row_tuple[key_int] )
        log.debug( 'len easya_keys, {}'.format(len(easya_keys)) )
        return easya_keys

    def _intersect_keys( self, rapid_keys, easya_keys):
        """ Runs set work.
            Called by update_production_table() """
        rapid_not_in_easya = list( sets.Set(rapid_keys) - sets.Set(easya_keys) )
        easya_not_in_rapid = list( sets.Set(easya_keys) - sets.Set(rapid_keys) )
        log.debug( 'rapid_not_in_easya, {}'.format(rapid_not_in_easya) )
        log.debug( 'easya_not_in_rapid, {}'.format(easya_not_in_rapid) )
        return ( rapid_not_in_easya, easya_not_in_rapid )

    def _add_rapid_entries( self, rapid_not_in_easya ):
        """ Runs inserts of new records.
            Called by update_production_table() """
        for rapid_key in rapid_not_in_easya:
            rapid_title = PrintTitleDev.objects.get( key=rapid_key )
            sql = '''
                INSERT INTO `{destination_table}` ( `key`, `issn`, `start`, `end`, `location`, `call_number` )
                VALUES ( '{key}', '{issn}', '{start}', '{end}', '{building}', '{call_number}' );
                '''.format( destination_table=unicode(os.environ['RAPID__TITLES_TABLE_NAME']), key=rapid_title.key, issn=rapid_title.issn, start=rapid_title.start, end=rapid_title.end, building=rapid_title.building, call_number=rapid_title.call_number )
            self.db_handler.run_sql( sql=sql, connection_url=settings_app.DB_CONNECTION_URL )
        log.debug( 'rapid additions to easyA complete' )
        return

    def _remove_easya_entries( self, easya_not_in_rapid ):
        """ Runs deletion of old records.
            Called by update_production_table() """
        for easya_key in easya_not_in_rapid:
            sql = '''
                DELETE FROM `{destination_table}`
                WHERE `key` = '{easya_key}'
                LIMIT 1;
                '''.format( destination_table=unicode(os.environ['RAPID__TITLES_TABLE_NAME']), easya_key=easya_key )
            self.db_handler.run_sql( sql=sql, connection_url=settings_app.DB_CONNECTION_URL )
        log.debug( 'easyA deletions complete' )
        return

    # def update_production_table( self ):
    #     """ Runs update-production sql.
    #         TODO: a more elegant way to do this would be to query both tables, do a set intersection, and then do the appropriate small loop of additions and deletes.
    #         Called by run_update() """
    #     ## load all new data to memory
    #     titles = PrintTitleDev.objects.all()
    #     ## iterate through source-set adding new records if needed
    #     for entry in titles:
    #         sql = '''
    #             SELECT * FROM `{destination_table}`
    #             WHERE `key` = '{key}'
    #             AND `issn` = '{issn}'
    #             AND `start` = {start}
    #             AND `end` = {end}
    #             AND `location` = '{location}'
    #             AND `call_number` = '{call_number}';
    #             '''.format( destination_table=unicode(os.environ['RAPID__TITLES_TABLE_NAME']), key=entry.key, issn=entry.issn, start=entry.start, end=entry.end, location=entry.location, call_number=entry.call_number )
    #         result = self.db_handler.run_sql( sql=sql, connection_url=settings_app.DB_CONNECTION_URL )
    #         if result == None:
    #             sql = '''
    #             INSERT INTO `{destination_table}` ( `key`, `issn`, `start`, `end`, `location`, `call_number` )
    #             VALUES ( '{key}', '{issn}', '{start}', '{end}', '{location}', '{call_number}' );
    #             '''.format( destination_table=unicode(os.environ['RAPID__TITLES_TABLE_NAME']), key=entry.key, issn=entry.issn, start=entry.start, end=entry.end, location=entry.location, call_number=entry.call_number )
    #             self.db_handler.run_sql( sql=sql, connection_url=settings_app.DB_CONNECTION_URL )
    #     ## iterate through destination-set deleting records if they're not in the source
    #     sql = '''SELECT * FROM `{}`;'''.format( unicode(os.environ['RAPID__TITLES_TABLE_NAME']) )
    #     result = self.db_handler.run_sql( sql=sql, connection_url=settings_app.DB_CONNECTION_URL )
    #     tuple_keys = {
    #         'key': 0, 'issn': 1, 'start': 2, 'end': 3, 'location': 4, 'call_number': 5 }
    #     for tuple_entry in result:
    #         match = PrintTitleDev.objects.filter(
    #             key=tuple_keys['key'], issn=tuple_keys['issn'], start=int(tuple_keys['start']), end=int(tuple_keys['end']), building=tuple_keys['location'], call_number=tuple_keys['call_number'] )
    #         if match == []:
    #             sql = '''
    #                 DELETE * FROM `{destination_table}`
    #                 WHERE `key` = '{key}'
    #                 AND `issn` = '{issn}'
    #                 AND `start` = {start}
    #                 AND `end` = {end}
    #                 AND `location` = '{location}'
    #                 AND `call_number` = '{call_number}'
    #                 LIMIT 1;
    #                 '''.format( destination_table=unicode(os.environ['RAPID__TITLES_TABLE_NAME']), key=entry.key, issn=entry.issn, start=entry.start, end=entry.end, location=entry.location, call_number=entry.call_number )
    #     return

    # end class UpdateTitlesHelper
