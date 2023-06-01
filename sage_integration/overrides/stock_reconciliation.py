import frappe
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import StockReconciliation, get_items_for_stock_reco,get_item_data
import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr, flt
from erpnext.stock.utils import get_stock_balance

class CustomStockStockReconciliation(StockReconciliation):
    
    def get_items_2(
        self, item_code, warehouse, ignore_empty_stock=True
    ):
        ignore_empty_stock = cint(ignore_empty_stock)
        items = [frappe._dict({"item_code": item_code, "warehouse": warehouse})]

        if not item_code:
            items = get_items_for_stock_reco(warehouse, self.company)

        res = []
        itemwise_batch_data = self.get_itemwise_batch2(warehouse)

        for d in items:
            if d.item_code in itemwise_batch_data:
                valuation_rate = get_stock_balance(
                    d.item_code, d.warehouse, self.posting_date, self.posting_time, with_valuation_rate=True
                )[1]

                for row in itemwise_batch_data.get(d.item_code):
                    if ignore_empty_stock and not row.qty:
                        continue

                    args = get_item_data(row, row.qty, valuation_rate)
                    res.append(args)
            else:
                stock_bal = get_stock_balance(
                    d.item_code,
                    d.warehouse,
                    self.posting_date,
                    self.posting_time,
                    with_valuation_rate=True,
                    with_serial_no=cint(d.has_serial_no),
                )
                qty, valuation_rate, serial_no = (
                    stock_bal[0],
                    stock_bal[1],
                    stock_bal[2] if cint(d.has_serial_no) else "",
                )

                if ignore_empty_stock and not stock_bal[0]:
                    continue

                args = get_item_data(d, qty, valuation_rate, serial_no)

                res.append(args)

        return res
    
    def get_itemwise_batch2(self, warehouse):
        from erpnext.stock.report.batch_wise_balance_history.batch_wise_balance_history import execute

        itemwise_batch_data = {}

        filters = frappe._dict(
            {"warehouse": warehouse, "from_date": self.posting_date, "to_date": self.posting_date, "company": self.company}
        )

        columns, data = execute(filters)

        for row in data:
            itemwise_batch_data.setdefault(row[0], []).append(
                frappe._dict(
                    {
                        "item_code": row[0],
                        "warehouse": row[3],
                        "qty": row[8],
                        "item_name": row[1],
                        "batch_no": row[4],
                    }
                )
            )

        return itemwise_batch_data
