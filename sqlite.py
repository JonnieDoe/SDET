#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""SQLite module."""


import sqlite3


class Sqlite(object):
    """SQLIte related tasks."""

    def __init__(self, sqlite_file=None) -> None:
        """Initialize the SQLite instance.
        :param sqlite_file: Path to the SQLite file [str]
        """
        self.__sqlite_file = sqlite_file
        self.__table_name = 'SDET'
        self.__table_header = 'Detail_Info,No_of_Executed_Tests,No_of_Failed_Tests,List_of_IDs,Run_Status'

    @property
    def sqlite_file(self) -> str:
        """Get the SQLite file."""
        return self.__sqlite_file

    @property
    def table_name(self):
        """Get the table name as in SQLite db."""
        return self.__table_name

    @property
    def table_header(self) -> str:
        """Get the table header."""
        return self.__table_header

    ################################################################################################
    def connect(self):
        """Connect to DB
        :return: Connection, on success
                 None, on failure
        """
        try:
            conn = sqlite3.connect(self.sqlite_file, detect_types=sqlite3.PARSE_DECLTYPES)
        except Exception as error:
            print("\nError when trying to connect to database: {db}\n\t{err}\n".format(db=self.sqlite_file, err=error))
            return
        else:
            return conn

    ################################################################################################
    def query_db(self, sql_query: str = None):
        """Select values from DB.
        :param sql_query: Query to use [str]
        :return ROWS, on success
                False, on failure
                None, if no input provided
        """

        if not sql_query:
            return

        connection = self.connect()
        with connection:
            cursor = connection.cursor()

            try:
                cursor.execute(sql_query)
            except Exception as err:
                print("\nError when trying to query table: [{table}]\n\t{err}\n".format(table=self.table_name, err=err))
                return False
            else:
                rows = cursor.fetchall()

                return rows

    ################################################################################################
    def insert_into_db(self, values_to_insert: tuple = None):
        """Insert values into DB.
        :param values_to_insert: Values to insert [tuple]
        :return True, on success
                False, on failure
                None, if no input provided
        """

        if not values_to_insert:
            return

        sql_query = (
            'INSERT INTO MAIN.{table}({header}) VALUES (?,?,?,?,?)'.format(table=self.table_name,
                                                                           header=self.table_header)
        )

        connection = self.connect()
        with connection:
            cursor = connection.cursor()

            try:
                cursor.execute(sql_query, values_to_insert)
            except Exception as err:
                print(
                    "\nError when trying to insert values into table: [{table}]\n\t{err}\n".format(
                        table=self.table_name, err=err)
                )
                return False
            else:
                connection.commit()

                return True


####################################################################################################
def main():
    """The main function."""
    pass


####################################################################################################
# Standard boilerplate to call the main() function to begin the program.
# This only runs if the module was *not* imported.
#
if __name__ == '__main__':
    main()
