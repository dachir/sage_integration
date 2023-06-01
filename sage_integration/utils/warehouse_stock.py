import frappe

frappe.whitelist()
def get_total_stock(code):
	return frappe.db.get_list("Bin", filters=[["actual_qty","!=",0],["item_code","=",code]], fields=["warehouse","item_code","actual_qty"])