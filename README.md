##### overview

- provides a web-interface to initiate and monitor a few rapid-admin tasks.


##### notes

- for reference: creating a backup table...

        CREATE TABLE `backup_table_name` (
            `key` varchar( 20 ) DEFAULT NULL ,
            `issn` varchar( 15 ) DEFAULT NULL ,
            `start` int( 11 )  DEFAULT NULL ,
            `end` int( 11 )  DEFAULT NULL ,
            `location` varchar( 25 ) DEFAULT NULL ,
            `call_number` varchar( 50 ) DEFAULT NULL
            );

---
