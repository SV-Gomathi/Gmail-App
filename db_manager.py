import datetime
import re
import sys
import logging
import mysql.connector

from db_config import db_config
from custom_exception import DBConnectionError, DBQueryError, DBIntegrityError


logger = logging.getLogger(__name__)


class MySqlDBManager:

    def __init__(self):
        self.connection_id = None
        self.conn = self.create_connection()

    def create_connection(self):
        """Getting MySQL Connection
        """

        try:
            database = db_config['dbname']
            user = db_config['user']
            passwd = db_config['password']
            host = db_config['host']
            port = int(db_config['port'])
            retry = db_config['retry']

        except Exception:
            print("exception while fetching config variable.")
            raise
        for trial in range(int(retry)):
            try:
                # Creating MySQL Connection
                self.conn = mysql.connector.connect(host=host,
                                                    user=user,
                                                    passwd=passwd,
                                                    db=database,
                                                    port=port,
                                                    autocommit=False)
                # Retrieving connection id from MySQL server
                self.connection_id = self.conn.connection_id
                return self.conn

            except (mysql.connector.DatabaseError,
                    mysql.connector.IntegrityError,
                    mysql.connector.InterfaceError,
                    mysql.connector.InternalError,
                    mysql.connector.OperationalError,
                    mysql.connector.PoolError,
                    mysql.connector.DataError,
                    mysql.connector.NotSupportedError,
                    mysql.connector.ProgrammingError) as ex:
                print(" Exception Occurred in creating Connection. exception no: %s", ex.errno)
                if trial == int(retry)-1:
                    print("Exception Occurred in creating Connection and retry limit reached")
                    raise DBConnectionError(ex.errno, "Database Connection Error : {}".format(ex))

    def getcursor(self):
        '''
           Creating cursor from the connection.
        '''
        if self.conn:
            # if self.cursor_type == "TUPLE_CURSOR":
            #     return self.conn.cursor()
            return self.conn.cursor(dictionary=True)

    def __formatargs(self, query, arguments):
        if isinstance(arguments, tuple):
            arguments = list(arguments)
        res_args = []
        if isinstance(arguments, list):
            end_idx = 0
            query = re.sub('\([ ]*%[ ]*s[ ]*\)', '(%s)', query)
            for i, value in enumerate(arguments):
                if isinstance(value, tuple) or isinstance(value, list):
                    len_ = len(value)
                    find_idx = query.index('(%s)', end_idx)
                    end_idx = find_idx + len("(%s)")
                    query = list(query)
                    query[find_idx:end_idx] = '(%s' + ', %s' * (len_ - 1) + ')'
                    query = ''.join(query)
                    for ele in value:
                        res_args.append(ele)
                else:
                    res_args.append(value)
        else:
            pass

        if not res_args:
            res_args = arguments
        return query, res_args

    def processquery(self, query, count=0, arguments=None, fetch=True, returnprikey=0, do_not_log_resultset=0):
        '''
        :Notes: execute the given query respective of given argument.
        :Args: query: query to execute
        :Args: count: if select query, howmany rows to return
        :Args: arguments: arguments for the query.
        :Args: fetch: select query - True , update/insert query - False
        :Args: returnprikey: insert query - 1, update query - 0
        '''

        try:
            curs = self.getcursor()
            if arguments:
                query, arguments = self.__formatargs(query, arguments)
            curs.execute(query, arguments)

            if fetch:
                result_set = curs.fetchall()
                if count == 1 and len(result_set) >= count:
                    res = result_set[0]
                elif count == 1 and len(result_set) < count:
                    res = {}
                elif len(result_set) >= count > 1:
                    res = result_set[0:count]
                else:
                    res = result_set
            else:
                if returnprikey:
                    res = curs.lastrowid
                else:
                    res = curs.rowcount
            curs.close()
            return res
        except mysql.connector.IntegrityError as ex:
            print("ConnectionID :: " +
                             str(self.connection_id) +
                             " Exception Occurred while executing the query")
            raise DBIntegrityError(ex.errno, 'Exception while executing the Query::%s' % ex)
        except (mysql.connector.DataError,
                mysql.connector.IntegrityError,
                mysql.connector.NotSupportedError,
                mysql.connector.ProgrammingError) as ex:
            print("ConnectionID :: " +
                             str(self.connection_id) +
                             " Exception Occurred while executing the query")
            raise DBQueryError(ex.errno, 'Exception while executing the Query::%s' % ex)
        except (mysql.connector.DatabaseError,
                mysql.connector.InterfaceError,
                mysql.connector.InternalError,
                mysql.connector.OperationalError,
                mysql.connector.PoolError) as ex:
            print("ConnectionID :: " +
                             str(self.connection_id) +
                             " Exception Occurred in creating Connection")
            raise DBConnectionError(ex.errno, 'DB Connection creation Error::%s' % ex)
        except ValueError as ex:
            print("ConnectionID :: " +
                             str(self.connection_id) +
                             " Value Error Occurred while executing the query")
            raise DBQueryError(None, 'Exception while executing the Query::%s' % ex)
        except Exception as ex:
            print("ConnectionID :: " +
                             str(self.connection_id) +
                             " Un-handled exception in DB Manager processquery")
            raise DBConnectionError(None, 'Un-handled exception in DB Manager processquery::%s' % ex)

