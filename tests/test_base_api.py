import sys
from os.path import join, abspath, pardir

import pytest
import unittest

from odoo_external_api import OdooBaseApi
from includes.config import username, password, url, db


class TestOdooBaseApi(unittest.TestCase):

    ac = OdooBaseApi(url, db, username, password)
    lot = "test_lot_in_odoo_db_being_tested"
    _id = 220541
    fields = "name, product_id"
    field = "name"
    value = "test_value"
    table = "stock.production.lot"
    where = f"""name='{lot}'"""

    def test_connection_return_object_if_correct(self):
        # test admin rights are correct, return if they are.
        assert self.ac.uid == 1
        return self.ac

    def test_user_access_rights(self):
        rights = self.ac.check_user_access_rights(raise_exception=True)
        assert rights == True

    def test_get_all_ids_type(self):
        assert isinstance(self.ac.get_all_ids(), list)

    def test_pprint_res_correct_field(self):
        field = self.ac.pprint_res([{"world": False, "hello": "World"}], field="world")
        assert field == True

    def test_pprint_res_error_field(self):
        msg = self.ac.pprint_res([{"world": False}], field="hello")
        assert msg == "Nothing to display"

    def test_pprint_res_correct_normal(self):
        non = self.ac.pprint_res([{"world": False, "hello": "World"}])
        assert non == True

    def test_pprint_res_error_normal(self):
        msg = self.ac.pprint_res([[{"world": False}]])
        assert msg == "Nothing to display"

    def test_base_execute_kw_parse_ids(self):
        ids, _ = self.ac.base_execute_kw_parse(1)
        assert isinstance(ids, list)

    def test_base_execute_kw_parse_ids_and_dict(self):
        ids, d = self.ac.base_execute_kw_parse(False, field="field", val="val")
        assert isinstance(ids, list) and isinstance(d, dict)

    def test_count_returns_int(self):
        count = self.ac.count_records([])
        assert isinstance(count, int)

    def test_read_records(self):
        read = self.ac.read_records([self._id])
        assert read[0]["name"] == self.lot

    def test_list_record_fields(self):
        d = self.ac.list_record_fields()
        assert isinstance(d, dict) and isinstance(d["name"], dict)

    def test_search_and_read(self):
        lot = self.ac.search_and_read([("id", "=", self._id)])
        assert (lot[0]["name"] == self.lot) and (lot[0]["id"] == self._id)

    def test_crud(self):
        def test_create_record(cls):
            p = cls.ac.create_record(
                dictionary={"name": "New Partner", "street": "Heaven"},
                table="res.partner",
            )

            assert isinstance(p, int)

            check = cls.ac.search_and_read([("id", "=", p)], table="res.partner")

            assert check[0]["name"] == "New Partner" and check[0]["street"] == "Heaven"

            return p

        def test_update_record(cls, crud_id):
            u = cls.ac.update_record(
                crud_id,
                dictionary={"name": "Changed", "street": "Hell"},
                table="res.partner",
            )

            assert u

            check = cls.ac.search_and_read([("id", "=", crud_id)], table="res.partner")

            assert check[0]["name"] == "Changed" and check[0]["street"] == "Hell"

        def test_delete_record(cls, crud_id):
            d = cls.ac.delete_record(crud_id, table="res.partner")

            # True
            assert d

            check = cls.ac.search_and_read([("id", "=", crud_id)], table="res.partner")
            # []
            assert not check

        crud_id = test_create_record(self)
        test_update_record(self, crud_id)
        test_delete_record(self, crud_id)

    def test_run_method(self):
        m = self.ac.run_method(
            "test_external_method",
            args=[[], "arg1", "arg2"],
            kwargs={"kw1": True, "kw2": True},
            table="imt.api.tests",
        )
        assert m == ["arg1", "arg2", True, True]

    def test_select_sql(self):
        query = self.ac.gen_select(self.fields, self.table, where=self.where)
        assert (
            query
            == """SELECT name, product_id FROM stock_production_lot WHERE name='test_lot_in_odoo_db_being_tested';"""
        )

    def test_update_sql(self):
        query = self.ac.gen_update(self.field, self.value, self.table, where=self.where)
        assert (
            query
            == """UPDATE stock_production_lot SET name='test_value' WHERE name='test_lot_in_odoo_db_being_tested';"""
        )

    def test_delete_sql(self):
        query = self.ac.gen_delete(self.table, where=self.where)
        assert (
            query
            == """DELETE FROM stock_production_lot WHERE name='test_lot_in_odoo_db_being_tested';"""
        )


#  The Following can be activated if a sql runnable method is invoked server side..
# def test_external_sql_found(self):
#     q = f"select name from stock_production_lot where id = {self._id}"
#     r = self.ac.ex_sql(query=q)
#     assert r[0]["name"] == self.lot

# def test_external_sql_return_false(self):
#     q = "select name from stock_production_lot where id = 2"
#     r = self.ac.ex_sql(queries=[q])
#     assert not r

# def
