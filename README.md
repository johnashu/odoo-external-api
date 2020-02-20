# odoo-external-api
[![Total alerts](https://img.shields.io/lgtm/alerts/g/johnashu/odoo-external-api.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/johnashu/odoo-external-api/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/johnashu/odoo-external-api.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/johnashu/odoo-external-api/context:python)

An Abstract Base Class to inherit from and interact with Odoos external XML-RPC API
 
Example Inheritance:

    from odoo_base_api import OdooBaseApi, username, password, url, db

    class StockProductionLot(OdooProductionApi):
        """ Class to handle stock.production.lot """

        def create_products(self, codes, product_id=9999):

            lots = {}

            for code in codes:
                lot = self.create_record(
                    table="stock.production.lot",
                    dictionary={
                        "name": code,
                        "product_id": product_id,
                        "product_qty": 0.0,
                        "product_uom_id": 1,
                        "company_id": 1,
                    },
                )

                lots[code] = lot

            return lots

    if __name__ == "__main__":
        spl = StockProductionLot(url, db, username, password, table='stock.production.lot')

Further Abstractions can be useful if method count is high in the main table class or for encapsulating complex alogirthms:
    
    from stock_move_line import StockMoveLine, username, password, db, url

    class CheckStockQuantity(StockMoveLine):
        ...

    from stock_production_lot import StockProductionLot, username, password, db, url

    class ChangeLabels(StockProductionLot):
        ...

You can also invoke multiple inheritence to marry 2 tables methods together and take advantage of unique situations.

    from mrp_production import MrpProduction, username, password, db, url
    from mrp_workorder import Workorders


    class CleanMo(Workorders, MrpProduction):
        pass

    mod = CleanMo(url, db, username, password)
    mod.change_workorder_state(mo_ids, "cancel")
    mo_names, mo_ids = mod.mark_as_cancelled_from_mo(mo_names)
    mod.delete_cancelled()




Contributions welcome.

Run `tox` from the commandline to pass tests.

Alternativley run:
`coverage run -m pytest -x tests`

Please aim for 100% coverage.

    Name                     Stmts   Miss  Cover   Missing
    ------------------------------------------------------
    includes\config.py           4      0   100%
    odoo_external_api.py        81      0   100%
    tests\test_base_api.py      85      0   100%
    ------------------------------------------------------
    TOTAL                      170      0   100%
