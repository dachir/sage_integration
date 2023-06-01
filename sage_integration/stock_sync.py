import frappe
from frappe.utils import getdate, nowtime
import pymssql


def stock_sync_kin():
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        """
        SELECT s.STOFCY_0, s.ITMREF_0, m.ITMDES1_0, s.LOC_0, SUM(s.QTYSTU_0) AS QTYSTU_0, i.AVC_0 
        FROM LIVE.STOCK s INNER JOIN LIVE.ITMMVT i ON s.ITMREF_0 = i.ITMREF_0 AND s.STOFCY_0 = i.STOFCY_0 
            INNER JOIN LIVE.ITMMASTER m ON m.ITMREF_0 = i.ITMREF_0
        WHERE s.STOFCY_0 = 'M0001' AND (m.TCLCOD_0 LIKE 'ENG%' OR m.TCLCOD_0 = 'MRKT')
        GROUP BY s.STOFCY_0, s.ITMREF_0, m.ITMDES1_0, s.LOC_0,i.AVC_0
        """
    )

    stock_doc = create_header()
    annule_stock(stock_doc)

    stock_doc = create_header()

    rows = []
    for row in cursor:
        item_args = frappe._dict({
            "item_code" : row['ITMREF_0'],
            "item_name" : row['ITMDES1_0'],
            "warehouse" : row['LOC_0'] + "_Sage - MES",
            "qty": row['QTYSTU_0'],
            "valuation_rate" : row['AVC_0'],
            "batch_no" : row['ITMREF_0'],
        })
        rows.append(item_args)

    if rows :
        stock_doc.update({ 'items': rows, })
        frappe.msgprint(str(stock_doc))
        stock_doc.insert()
        stock_doc.submit()
        frappe.db.commit()
    else:
        frappe.db.rollback()

def create_header():
    return frappe.get_doc({
        'doctype': 'Stock Reconciliation',
        "company": "Marsavco Engg Stock",
        "purpose": "Stock Reconciliation",
        "branch" : "Kinshasa",
        "posting_date": getdate(),
        "posting_time": nowtime(),
    })

def annule_stock(stock_doc):
    items = stock_doc.get_items_2(None, "Sage - MES")
    rows = []
    for i in items:
        item_args = frappe._dict({
            "item_code" : i["item_code"],
            "item_name" : i["item_name"],
            "warehouse" : i["warehouse"],
            "qty": 0,
            "valuation_rate" : i["valuation_rate"],
            "batch_no" : i["batch_no"],
        })
        rows.append(item_args)

    if rows :
        stock_doc.update({ 'items': rows, })
        frappe.msgprint(str(stock_doc))
        stock_doc.insert()
        stock_doc.submit()
        frappe.db.commit()
    else:
        frappe.db.rollback()