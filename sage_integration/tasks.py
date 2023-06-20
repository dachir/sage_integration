import frappe
import pymssql
from striprtf.striprtf import rtf_to_text
from sage_integration.stock_sync import call_stock

def Rtf_to_text(rtf):
    #rtf = r"{\rtf1\ansi{\fonttbl{\f0 MS Sans Serif;}}\uc0\pard\fs24\pard\ql Material for fumigation Operations in small areas. \par}"
    text = rtf_to_text(rtf)
    return text

def all():
    pass

#def around_23_0():
#    stock_sync_kin()

def cron():
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    conn2 = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    up_cursor = conn2.cursor()

    cursor.execute('SELECT * FROM LIVE.ITMMASTER WHERE ZSYNC_0 < 3')
    for row in cursor:
        #print("ID=%s, Name=%s" % (row['ITMREF_0'], row['ITMDES1_0']))
        nb = frappe.db.count('Item', {'name': row['ITMREF_0']})
        if nb == 0: 
            item_name = row['ITMDES1_0']
            if len(row['ITMDES2_0']) > 1:
                item_name += " " + row['ITMDES2_0']
            if len(row['ITMDES3_0']) > 1:
                item_name += " " + row['ITMDES3_0']

            description = None
            if len(row['PURTEX_0']) > 1:
                conn3 = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12") 
                cursor3 = conn3.cursor(as_dict=True)
                cursor3.execute('SELECT TEXTE_0 FROM LIVE.TEXCLOB WHERE CODE_0 = %s;', row['PURTEX_0'] )
                for row3 in cursor3:
                    description = Rtf_to_text(row3['TEXTE_0'].replace('\u2103', '°C'))
                conn3.close()
            if row['TCLCOD_0'] == 'FA':
                args = frappe._dict({
                    'doctype': 'Item',
                    'item_code': row['ITMREF_0'],
                    'item_name': item_name,
                    'item_group': row['TCLCOD_0'],
                    'stock_uom': row['STU_0'],
                    'is_stock_item': 0,
                    'is_fixed_asset': 1,
                    'asset_category': row['ACCCOD_0'],
                    #'category': row['TSICOD_0'],
                    #'sub_category': row['TSICOD_1'],
                    #'sub_category_2': row['TSICOD_2'],
                })
            elif row['TSICOD_0'] == None or len(row['TSICOD_0']) == 1:
                args = frappe._dict({
                    'doctype': 'Item',
                    'item_code': row['ITMREF_0'],
                    'item_name': item_name,
                    'item_group': row['TCLCOD_0'],
                    'stock_uom': row['STU_0'],
                    'has_batch_no': 1,
                    'create_new_batch': 1,
                    'has_expiry_date': 1 if row['TCLCOD_0'] in ['FG','TG','CHEM'] else 0,
                    #'category': row['TSICOD_0'],
                    #'sub_category': row['TSICOD_1'],
                    #'sub_category_2': row['TSICOD_2'],
                })
            elif row['TSICOD_1'] == None  or len(row['TSICOD_1']) == 1:
                args = frappe._dict({
                    'doctype': 'Item',
                    'item_code': row['ITMREF_0'],
                    'item_name': item_name,
                    'item_group': row['TCLCOD_0'],
                    'stock_uom': row['STU_0'],
                    'has_batch_no': 1,
                    'create_new_batch': 1,
                    'has_expiry_date': 1 if row['TCLCOD_0'] in ['FG','TG','CHEM'] else 0,
                    'shelf_life_in_days': 365,
                    'category': row['TSICOD_0'],
                    #'sub_category': row['TSICOD_1'],
                    #'sub_category_2': row['TSICOD_2'],
                })
            elif row['TSICOD_2'] == None  or len(row['TSICOD_2']) == 1:
                args = frappe._dict({
                    'doctype': 'Item',
                    'item_code': row['ITMREF_0'],
                    'item_name': item_name,
                    'item_group': row['TCLCOD_0'],
                    'stock_uom': row['STU_0'],
                    'has_batch_no': 1,
                    'create_new_batch': 1,
                    'has_expiry_date': 1 if row['TCLCOD_0'] in ['FG','TG','CHEM'] else 0,
                    'shelf_life_in_days': 365,
                    'category': row['TSICOD_0'],
                    'sub_category': row['TSICOD_1'],
                    #'sub_category_2': row['TSICOD_2'],
                })
            else :
                args = frappe._dict({
                    'doctype': 'Item',
                    'item_code': row['ITMREF_0'],
                    'item_name': row['ITMDES1_0'],
                    'item_group': row['TCLCOD_0'],
                    'stock_uom': row['STU_0'],
                    'has_batch_no': 1,
                    'create_new_batch': 1,
                    'has_expiry_date': 1 if row['TCLCOD_0'] in ['FG','TG','CHEM'] else 0,
                    'shelf_life_in_days': 365,
                    'category': row['TSICOD_0'],
                    'sub_category': row['TSICOD_1'],
                    'sub_category_2': row['TSICOD_2'],
                })
            
            if description != None :
                args.update({ 'description': description, })

            if row['TCLCOD_0'] in ['FG','TG']:
                if row['PCU_0'] != None and len(row['PCU_0']) > 1 and row['PCU_1'] != None and len(row['PCU_1']) > 1: 
                    args.update({'uoms' : [{
                        'uom': row['PCU_0'],
                        'conversion_factor': row['PCUSTUCOE_0'],
                    },{
                        'uom': row['PCU_1'],
                        'conversion_factor': row['PCUSTUCOE_1'],
                    }]})
                elif row['PCU_0'] != None and len(row['PCU_0']) > 1 and (row['PCU_1'] == None or len(row['PCU_1']) == 1): 
                    args.update({'uoms' : [{
                        'uom': row['PCU_0'],
                        'conversion_factor': row['PCUSTUCOE_0'],
                    }]})
            
            #print(args)
            frappe.get_doc(args).insert()
            if row['TCLCOD_0'] != 'FA':
                frappe.get_doc({"doctype": "Batch", "batch_id": row['ITMREF_0'], "item" : row['ITMREF_0']}).insert()
            frappe.db.commit()
            up_cursor.execute('UPDATE LIVE.ITMMASTER SET ZSYNC_0 = 3 WHERE ITMREF_0 = %s;', row['ITMREF_0'])
            conn2.commit()

    conn.close()
    conn2.close()

def hourly():
    pass
def daily():
    call_stock()


def weekly():
    pass
def monthly():
    pass

