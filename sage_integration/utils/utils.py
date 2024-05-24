import frappe
from frappe.utils import getdate
import pymssql

def share_doc(doc):
    if doc.workflow_state != "Draft":
        users = frappe.db.sql(
            """
            SELECT DISTINCT h.parent
            FROM `tabWorkflow Transition` t INNER JOIN tabRole r ON r.name = t.allowed INNER JOIN `tabHas Role` h ON h.role = r.name
            WHERE t.parent = %s AND t.state = %s
            """, (doc.doctype, doc.workflow_state), as_dict =1
        )

        #if not frappe.has_permission(doc=doc, ptype="submit", user=users[0].parent):
        frappe.share.add_docshare(
            doc.doctype, doc.name, users[0].parent, submit=1, flags={"ignore_share_permission": True}
        )
        frappe.db.commit()

@frappe.whitelist()
def get_sage_selling_price(site,item):
    if site == 'Kinshasa':
        site = 'M0001'
    else:
        site = 'M0002'

    end_of_year = str(getdate().year) + "-12-31"
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute("SELECT PLICRI1_0, PRI_0 AS cout_pc FROM LIVE.SPRICLIST INNER JOIN LIVE.ITMMASTER ON ITMREF_0 = PLICRI1_0 WHERE PLI_0 = 'T01' AND PLICRI2_0 = %s AND PLIENDDAT_0 = %s  AND PLICRI1_0 = %s", (site, end_of_year, item))
    row = cursor.fetchone()
    conn.close()
    if row:
        #frappe.msgprint(str(row['cout_pc']))
        return row['cout_pc']
    return 0


@frappe.whitelist()
def get_sage_item_cost(site,item):
    if site == 'Kinshasa':
        site = 'M0001'
    else:
        site = 'M0002'

    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute('SELECT i.ITMREF_0, i.TCLCOD_0, m.AVC_0 cout_tn, m.AVC_0 * CASE WHEN i.PCUSTUCOE_0 = 0 THEN 1 ELSE i.PCUSTUCOE_0 END AS  cout_ct, m.AVC_0 * CASE WHEN i.PCUSTUCOE_1 = 0 THEN 1 ELSE i.PCUSTUCOE_1 END AS cout_pc FROM LIVE.ITMMASTER i INNER JOIN LIVE.ITMMVT m ON m.ITMREF_0 = i.ITMREF_0   WHERE m.STOFCY_0 = %s AND i.ITMREF_0 = %s', (site,item))
    row = cursor.fetchone()
    conn.close()
    if row:
        #frappe.msgprint(str(row['cout_pc']))
        return row['cout_pc']
    return 0
    
@frappe.whitelist()
def get_sage_item_cost_stu(site, item):
    if site == 'Kinshasa':
        site = 'M0001'
    else:
        site = 'M0002'

    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute('SELECT i.ITMREF_0, i.TCLCOD_0, m.AVC_0 cout_tn, i.SAUSTUCOE_0 conv, m.AVC_0 * CASE WHEN i.PCUSTUCOE_0 = 0 THEN 1 ELSE i.PCUSTUCOE_0 END AS cout_ct, m.AVC_0 * CASE WHEN i.PCUSTUCOE_1 = 0 THEN 1 ELSE i.PCUSTUCOE_1 END AS cout_pc FROM LIVE.ITMMASTER i INNER JOIN LIVE.ITMMVT m ON m.ITMREF_0 = i.ITMREF_0   WHERE m.STOFCY_0 = %s AND i.ITMREF_0 = %s', (site,item))
    row = cursor.fetchone()
    conn.close()
    if row:
        # Extract the desired values from the row dictionary
        cout_tn = row['cout_tn']
        cout_pc = row['conv']
        return cout_tn, cout_pc  # Return both values as a tuple
    return 0, 0  # Return default values if no row is found



@frappe.whitelist()
def get_sage_cm29_price(item):
    end_of_year = str(getdate().year) + "-12-31"

    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute("SELECT PLICRI1_0, PRI_0, PRI_0 * (1-(DCGVAL_0 + DCGVAL_1 + DCGVAL_2 + DCGVAL_3 + DCGVAL_4 + DCGVAL_5 + DCGVAL_6 + DCGVAL_7 + DCGVAL_8)/100) AS price FROM LIVE.SPRICLIST INNER JOIN LIVE.ITMMASTER ON ITMREF_0 = PLICRI1_0 WHERE PLI_0 = 'T511' AND PLICRI2_0  = '040' AND PLIENDDAT_0 = %s AND PLICRI1_0 = %s", (end_of_year,item))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['price']
    return 0

def get_string_part(input_string, part=0):
    # Split the string by " - " and take the first part
    parts = input_string.split(" - ")
    return parts[part] if parts else None