import frappe
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from sage_integration.utils.soap_ws import create_issue

class CustomStockEntry(StockEntry):
    
    def on_submit(self):
        super().on_submit()
        nb = frappe.db.sql(
					"""
						SELECT COUNT(*) AS nombre
                        FROM `tabStock Entry Detail`
                        WHERE parent = %(name)s AND s_warehouse LIKE %(warehouse)s
					""",
					{ "name":self.name, "warehouse": "%_Sage%" },
					as_dict =True,
				)[0].nombre
        if nb == 0 :
            return
        
        if self.stock_entry_type == "Material Issue":
            self.sage_code = create_issue(self.name)



