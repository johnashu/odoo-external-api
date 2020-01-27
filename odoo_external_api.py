import sys
from os.path import join, abspath, pardir

sys.path.append(abspath(pardir))
sys.path.append(join(abspath(pardir), ".."))

from add_paths import *
from xmlrpc.client import ServerProxy, ProtocolError, Error
from os.path import join, abspath, pardir
from ast import literal_eval
import logging as log

import pandas as pd

log.basicConfig(format="%(message)s", level=log.INFO)


from includes.config.config import (
    url,
    db,
    username,
    password,
    username_a2m,
    password_a2m,
)

from includes.config.magic_numbers import *


URL = "https://products.intermodaltelematics.com/?id={}"
current_table = "stock.production.lot"

# 'product.product'
# 'sale.order.line'
# 'sale.order'
# 'mrp.production'
# 'mrp.workorder'
# res.partner'
# 'purchase.order'


class OdooBaseApi:
    """ Class to communicate with Odoo from the Backend.
        Just a note here to remember to not include None but False in calls 
    """

    def __init__(self, url, db, user, password, table=current_table):
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.table = table

        # The xmlrpc/2/common endpoint provides meta-calls which don't require authentication,
        # such as the authentication itself or fetching version information.
        self.common = ServerProxy(f"{self.url}/xmlrpc/2/common")

        # The second endpoint is xmlrpc/2/object, is used to call methods of odoo models
        # via the execute_kw RPC function.Each call to execute_kw takes the following parameters:
        # the dbase to use, a string
        # the user id (retrieved through authenticate), an integer
        # the user's password, a string
        # the model name, a string
        # the method name, a string
        # an array/list of parameters passed by position
        # a mapping/dict of parameters to pass by keyword (optional)

        self.models = ServerProxy(f"{self.url}/xmlrpc/2/object")

        self.uid = self.common.authenticate(self.db, self.user, self.password, {})

        log.info(
            f"\n\n\tid  ::  ({self.uid})  {self.user}  ::  {self.db}  ::  LOGIN SUCCESSSFUL!!\n\n"
        )

    def check_user_access_rights(
        self, table=current_table, access_type="read", raise_exception=False
    ):
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            table,
            "check_access_rights",
            [access_type],
            {"raise_exception": raise_exception},
        )

    def get_all_ids(self):
        return self.search_records([], table=self.table)

    def pprint_res(self, d, field=None):
        """ 
            Takes in a list of dictionaries (d) 
            pretty prints the results to the terminal
        """
        for x in d:
            print()
            print("-" * 100)
            try:
                if field:
                    print(x[field])
                else:
                    for k, v in x.items():
                        print(f"\n\t{k}  ::  {v}")
            except (KeyError, IndexError, AttributeError) as e:
                msg = "Nothing to display"
                return msg

        print()
        print("-" * 100)
        print()
        return True

    def base_execute_kw_parse(self, ids, dictionary=False, field=False, val=False):

        d = {}

        if not dictionary:
            d[field] = val
        else:
            d = dictionary

        if not isinstance(ids, list):
            ids = [ids]

        return ids, d

    def search_records(self, query_list, table=current_table, offset=0, limit=0):
        """ Search will return the ID of the Records found """
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            table,
            "search",
            [query_list],
            {"offset": offset, "limit": limit},
        )

    def count_records(self, query_list, table=current_table):
        """  
            Calling search then search_count (or the other way around) may not yield coherent results         
            if other users are using the server: stored data could have changed between the calls.
        """
        return self.models.execute_kw(
            self.db, self.uid, self.password, table, "search_count", [query_list]
        )

    def read_records(self, ids, table=current_table, fields=False):
        """ 
            Read records: 
            # Record data is accessible via the read() method, which takes a list of ids 
            # (as returned by search()) and optionally a list of fields to fetch. 
            # By default, it will fetch all the fields the current user can read, 
            # which tends to be a huge amount.
        """
        ids, _ = self.base_execute_kw_parse(ids)
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            current_table,
            "read",
            [ids],
            {"fields": fields},
        )

    def list_record_fields(self, table=current_table, attrs=False):
        """ 
        Listing record fields:
        fields_get() can be used to inspect a model's fields and check which ones seem to be of interest.
        Because it returns a large amount of meta-information (it is also used by client programs) 
        it should be filtered before printing, the most interesting items for a human user are:

        string (the field's label), 
        help (a help text if available) and 
        type (to know which values to expect, or to send when updating a record)

        """
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            table,
            "fields_get",
            [],
            {"attributes": attrs},
        )

    def search_and_read(
        self, query_list, table=current_table, fields=False, offset=0, limit=0
    ):
        """
         Search and read
         Because it is a very common task, Odoo provides a search_read() shortcut 
         which as its name suggests is equivalent to a search() followed by a read(), 
         but avoids having to perform two requests and keep ids around.
         Its arguments are similar to search()'s, but it can also take a list of fields (like read(),
         if that list is not provided it will fetch all fields of matched records)

        """

        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            table,
            "search_read",
            [query_list],
            {"fields": fields, "offset": offset, "limit": limit},
        )

    def create_record(
        self, table=current_table, field=None, val=None, dictionary=False
    ):
        """ 
            Create a new record in the specified table 
            Takes in either a field and value or a dictionary of fields and values
            {'name': "New Partner", "address": "Heaven"}
        """
        ids, d = self.base_execute_kw_parse(
            False, field=field, val=val, dictionary=dictionary
        )

        return self.models.execute_kw(
            self.db, self.uid, self.password, table, "create", [d]
        )

    def update_record(
        self, ids, table=current_table, field=None, val=None, dictionary=False
    ):
        """ 
            Update a record based on Id.
             Takes in a single Id or a list of ids
             Takes in either a field and value or a dictionary of fields and values
            {'name': "New Partner", "address": "Heaven"}

        """
        ids, d = self.base_execute_kw_parse(
            ids, field=field, val=val, dictionary=dictionary
        )

        return self.models.execute_kw(
            self.db, self.uid, self.password, table, "write", [ids, d]
        )

    def delete_record(self, ids, table=current_table):
        """ 
            Delete a Record based on Id .
            Takes in a single Id or a list of ids

        """
        ids, _ = self.base_execute_kw_parse(ids)

        return self.models.execute_kw(
            self.db, self.uid, self.password, table, "unlink", [ids]
        )

    def run_method(self, method, args=[], kwargs={}, table=current_table):
        """ 
        Execute a method in the table passed on an odoo server.

        Takes in a method to execute and then  `ids` as a list of ids (can be only 1).  
        Beginning with a list of ids followed by any arguments.

        Example:

        models.execute_kw(db, 
        uid, 
        password, 
        table, 
        method, 
        [[list of ids], arg1, arg2...], {key: value}
        )

        Each call to execute_kw takes the following parameters:
            the dbase to use, a string
            the user id (retrieved through authenticate), an integer
            the user’s password, a string
            the model name, a string
            the method name, a string
            an array/list of parameters passed by position
            a mapping/dict of parameters to pass by keyword (optional)

        """
        return self.models.execute_kw(
            self.db, self.uid, self.password, table, method, args, kwargs
        )

    # def ex_sql(self, query=False, queries=False):
    #     # create a server-side method to run sql.. 
    #     return self.run_method(
    #         "run_query",
    #         args=[[]],
    #         kwargs={"query": query, "queries": queries},
    #         table="tools.sql",
    #     )

    def gen_select(self, fields, table, where=''): 
        query = f"SELECT {fields} FROM {table.replace('.', '_')} {where};"
        print(query)
        return query

    def gen_update(self, field, value, table, where=''):
        query = f"UPDATE {table.replace('.', '_')} SET {field}='{value}' {where};"
        print(query)
        return query        

    def gen_delete(self, table, where=''):
        query = f"DELETE FROM {table.replace('.', '_')} {where};"
        print(query)
        return query        


