import sys
from xmlrpc.client import ServerProxy, ProtocolError, Error
from os.path import join, abspath, pardir
from ast import literal_eval
import logging as log
log.basicConfig(format="%(message)s", level=log.CRITICAL)


db = ""
url = f"https://{db}.dev.odoo.com" # Odoo.sh address
username = ''
password = ''


URL = "https://products.intermodaltelematics.com/?id={}"
current_table = "stock.production.lot"

# 'product.product'
# 'sale.order.line'
# 'sale.order'
# mrp.production'
# 'mrp.workorder'
# res.partner'
# purchase.order


class ApiConnection:
    """ Class to communicate with Odoo from the Backend.
        Just a note here to remember to not include None but False in calls 
    """

    def __init__(self, url, db, user, password):
        self.url = url
        self.db = db
        self.user = user
        self.password = password

        # The xmlrpc/2/common endpoint provides meta-calls which don't require authentication,
        # such as the authentication itself or fetching version information.
        self.common = ServerProxy(f"{self.url}/xmlrpc/2/common")

        # The second endpoint is xmlrpc/2/object, is used to call methods of odoo models
        # via the execute_kw RPC function.Each call to execute_kw takes the following parameters:
        # the database to use, a string
        # the user id (retrieved through authenticate), an integer
        # the user's password, a string
        # the model name, a string
        # the method name, a string
        # an array/list of parameters passed by position
        # a mapping/dict of parameters to pass by keyword (optional)

        self.models = ServerProxy(f"{self.url}/xmlrpc/2/object")

    def auth_user(self):
        """ Autheticate the current user"""
        self.uid = self.common.authenticate(self.db, self.user, self.password, {})
        return self.uid

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

            TODO: Check out error thrown when passing in more than 1 id!!
        """
        [record] = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            current_table,
            "read",
            [ids],
            {"fields": fields},
        )
        return [record]

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
        # print("Searching and Reading..")  # check logging..
        # try:
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            table,
            "search_read",
            [query_list],
            {"fields": fields, "offset": offset, "limit": limit},
        )
        # except (ProtocolError, Error):
        #     print(f'ERROR, {ProtocolError}')
        #     return False

    def create_record(
        self, table=current_table, field=None, val=None, dictionary=False
    ):
        """ 
            Create a new record in the specified table 
            Takes in either a field and value or a dictionary of fields and values
            {'name': "New Partner", "address": "Heaven"}
        """
        d = {}
        if not dictionary:
            d[field] = val
        else:
            d = dictionary
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
        d = {}
        if not dictionary:
            d[field] = val
        else:
            d = dictionary

        if not isinstance(ids, list):
            ids = [ids]
        return self.models.execute_kw(
            self.db, self.uid, self.password, table, "write", [ids, d]
        )

    def delete_record(self, ids, table=current_table):
        """ 
            Delete a Record based on Id .
            Takes in a single Id or a list of ids

        """
        if not isinstance(ids, list):
            ids = [ids]
        return self.models.execute_kw(
            self.db, self.uid, self.password, "{}".format(table), "unlink", [ids]
        )

    def check_one_record(self, id, table=current_table):
        """ Checks one record based on Id """
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "{}".format(table),
            "search",
            [[["id", "=", id]]],
        )

    def auto_validate(self, ids, meth, table=current_table):
        """ 
        Execute the pressing of a button in odoo based upon the method used.

        Takes in a method to execute and then  `ids` as a list of ids (can be only 1).  
        Beginning with a list of ids followed by any arguments.

        Example:

        models.execute_kw(db, 
        uid, 
        password, 
        table, 
        method, 
        [[list of ids], arg1, arg2...]
        )

        Each call to execute_kw takes the following parameters:
            the database to use, a string
            the user id (retrieved through authenticate), an integer
            the user’s password, a string
            the model name, a string
            the method name, a string
            an array/list of parameters passed by position
            a mapping/dict of parameters to pass by keyword (optional)

        """
        # if not isinstance(ids, list):
        #     ids = [ids]
        return self.models.execute_kw(
            self.db, self.uid, self.password, table, meth, ids
        )

def pprint_res(d, field=None):
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
        except (KeyError, IndexError):
            print("Nothing to display")
            pass
    print()
    print("-" * 100)
    print()

def login_auth(db=db, username=username, password=password):
    """ function to log into Odoo.
        **kw to override username, password and db
    """
    url = f"https://{db}.dev.odoo.com"

    ac = ApiConnection(url, db, username, password)

    try:
        # AUTH AND RETURN ID
        uid = ac.auth_user()
        print(
            f"\n\n\tid  ::  ({uid})  {username}  ::  {db}  ::  LOGIN SUCCESSSFUL!!\n\n"
        )
        return ac
    except ProtocolError as e:
        print(e)

def get_ac(db=None):
    """ returns a connection object from the required database, defaults to master if no other database is passed """
    return login_auth(
        db=db if db else "imt-p-master-166492", username=username, password=password
    )

if __name__ == '__main__':
    ac = get_ac()

    ml = ac.search_and_read(
        [
            [
                'id', '=', 396
            ],
        ],
    table="res.partner",
    fields=['name', 'email', 'phone']
    )

    pprint_res(ml)
