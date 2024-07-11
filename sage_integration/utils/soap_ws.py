import frappe
import zeep
import requests
import xml.etree.ElementTree as ET
from frappe.utils import getdate
import json
import pymssql
from lxml import etree
import html
from sage_integration.utils.utils import get_string_part

############################### SOAP HEADERS ##################################################
def define_header_json():
    client = zeep.Client('http://dc7-web.marsavco.com:8124/soap-wsdl/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC?wsdl')
    client.transport.session.auth = requests.auth.HTTPBasicAuth('kossivi', 'A2ggrb012345-')
    # Set up context
    CContext = {
        'codeLang': 'ENG',
        'poolAlias': 'LIVE',
        'requestConfig': 'adxwss.trace.on=on&adxwss.trace.size=16384&adonix.trace.on=on&adonix.trace.level=3&adonix.trace.size=8&adxwss.optreturn=JSON&adxwss.beautify=true',
    }

    return CContext, client

def define_header_xml():
    client = zeep.Client('http://dc7-web.marsavco.com:8124/soap-wsdl/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC?wsdl')
    client.transport.session.auth = requests.auth.HTTPBasicAuth('kossivi', 'A2ggrb012345-')
    # Set up context
    CContext = {
        'codeLang': 'ENG',
        'poolAlias': 'LIVE',
        'requestConfig': 'adxwss.trace.on=on&adxwss.trace.size=16384&adonix.trace.on=on&adonix.trace.level=3&adonix.trace.size=8',
    }

    return CContext, client

############################### PURCHASE REQUEST ##################################################
def create_xml_doc(pr_doc):
    root_xml = ET.Element("PARAM")
    #root_xml.attrib["action"] = "create"

    #branch = frappe.db.get_list("Material Request Item", filters={'parent': pr_doc.name}, fields=["Max(branch) as branch"])[0].branch
    
    branch_doc = frappe.db.sql(
        """
            SELECT Max(branch) as branch
            FROM `tabMaterial Request Item`
            WHERE parent = %s
        """, (pr_doc.name), as_dict = 1
    )
    branch = branch_doc[0].branch

    ET.SubElement(root_xml, 'FLD', {'NAME': 'PSHFCY'}).text  = "M0001" if branch == "Kinshasa" else "M0002"



    if pr_doc.owner == 'Administrator':
        requester = 'ADMIN'
    else:
        requester = frappe.get_value("Employee",{"user_id":pr_doc.owner},"sage_code")
    ET.SubElement(root_xml, 'FLD', {'NAME': 'REQUSR'}).text = requester

    nb = frappe.db.count('Material Request Item', {'parent': pr_doc.name})
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'PSH1_1', 'SIZE': str(nb)})
    i = 0
    for item in pr_doc.items:
        i = i+ 1
        line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
        product = ET.SubElement(line, 'FLD', {'NAME': 'ITMREF', 'TYPE': 'Char'})
        product.text = item.item_code
        date = ET.SubElement(line, 'FLD', {'NAME': 'EXTRCPDAT', 'TYPE': 'Date'})
        date.text = getdate().strftime('%d/%m/%Y')
        qty = ET.SubElement(line, 'FLD', {'NAME': 'QTYPUU', 'TYPE': 'Decimal'})  
        qty.text = str(item.qty)
        cost_center = ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'})
        cost_center.text = item.cost_center.split(" - ")[0]

    return root_xml



def create_pr(name):
    pr_doc = frappe.get_doc("Material Request", name)
    
    xmlInput = create_xml_doc(pr_doc)
    CContext, client = define_header_xml()

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName='ZPSR', objectXml=ET.tostring(xmlInput))

    result = data.resultXml
    if result:
        xmlInput2 = ET.fromstring(result)
    else:
        xmlInput2 = process_sage_response(data)
    #test = ET.tostring(xmlInput)
    #frappe.msgprint(test.decode())
    code = xmlInput2.findall(".//GRP[@ID='PSH0_1']/FLD[@NAME='PSHNUM']")[0].text
    
    conn2 = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    up_cursor = conn2.cursor()
    up_cursor.execute('UPDATE LIVE.PREQUIS SET APPFLG_0 = 3 WHERE PSHNUM_0 = %s;', code)
    up_cursor.execute('UPDATE LIVE.PREQUISD SET LINAPPFLG_0 = 3 WHERE PSHNUM_0 = %s;', code)
    conn2.commit()
    conn2.close()

    return code

############################### STOCK ISSUE ##################################################
def create_issue_xml_doc(is_doc):
    root_xml = ET.Element("PARAM")
    #root_xml.attrib["action"] = "create"

    ET.SubElement(root_xml, 'FLD', {'NAME': 'STOFCY'}).text  = "M0001" if is_doc.branch == "Kinshasa" else "M0002"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'VCRDES'}).text  = is_doc.name

    nb = frappe.db.count('Material Request Item', {'parent': is_doc.name})
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'SMO1_1', 'SIZE': str(nb)})
    i = 0
    for item in is_doc.items:
        if "_Sage" in item.s_warehouse:
            i = i+ 1
            line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
            product = ET.SubElement(line, 'FLD', {'NAME': 'ITMREF', 'TYPE': 'Char'})
            product.text = item.item_code
            qty = ET.SubElement(line, 'FLD', {'NAME': 'QTYPCU', 'TYPE': 'Decimal'})
            qty.text = str(item.qty)
            location = ET.SubElement(line, 'FLD', {'NAME': 'LOC', 'TYPE': 'Char'})
            location.text = item.s_warehouse.split("_")[0]
            status = ET.SubElement(line, 'FLD', {'NAME': 'STA', 'TYPE': 'Char'})
            status.text = "A"
            line_desc = ET.SubElement(line, 'FLD', {'NAME': 'MVTDES', 'TYPE': 'Char'})
            line_desc.text = item.description[:30]
            cost_center = ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'})
            cost_center.text = item.cost_center.split(" - ")[0]
        

    return root_xml

def create_issue(name,public_name='ZSMO'):
    is_doc = frappe.get_doc("Stock Entry", name)
    xmlInput = create_issue_xml_doc(is_doc)
    CContext, client = define_header_xml()

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName=public_name, objectXml=ET.tostring(xmlInput))

    result = data.resultXml
    xmlInput2 = ET.fromstring(result)
    code = xmlInput2.findall(".//GRP[@ID='SMO0_1']/FLD[@NAME='VCRNUM']")[0].text

    return code

############################### RECEIPTION ##################################################
def create_issue_from_reception_in_sage(rec_num):
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute('SELECT d.ITMREF_0, d.QTYSTU_0, MIN(s.LOC_0) AS LOC_0, MIN(s.STA_0) AS STA_0 FROM LIVE.PRECEIPTD d INNER JOIN LIVE.STOJOU s ON s.STOFCY_0 = d.PRHFCY_0 AND d.PTHNUM_0 = s.VCRNUM_0 AND d.PTDLIN_0 = s.VCRLIN_0 WHERE PTHNUM_0 = %s GROUP BY d.ITMREF_0, d.QTYSTU_0;', rec_num)

    root_xml = ET.Element("PARAM")
    ET.SubElement(root_xml, 'FLD', {'NAME': 'STOFCY'}).text  = 'M0001'
    ET.SubElement(root_xml, 'FLD', {'NAME': 'VCRDES'}).text  = rec_num
    rows = cursor.fetchall()
    num_rows = len(rows)
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'SMO1_1', 'SIZE': str(num_rows)})

    i = 0
    cursor.execute('SELECT d.ITMREF_0, d.QTYSTU_0, MIN(s.LOC_0) AS LOC_0, MIN(s.STA_0) AS STA_0 FROM LIVE.PRECEIPTD d INNER JOIN LIVE.STOJOU s ON s.STOFCY_0 = d.PRHFCY_0 AND d.PTHNUM_0 = s.VCRNUM_0 AND d.PTDLIN_0 = s.VCRLIN_0 WHERE PTHNUM_0 = %s GROUP BY d.ITMREF_0, d.QTYSTU_0;', rec_num)
    for row in cursor:
        conn2 = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
        cursor2 = conn2.cursor(as_dict=True)
        cursor2.execute("SELECT i.ITMREF_0, i.TCLCOD_0, m.AVC_0 FROM LIVE.ITMMASTER i INNER JOIN LIVE.ITMMVT m ON m.ITMREF_0 = i.ITMREF_0 WHERE m.STOFCY_0 = 'M0001' AND i.ITMREF_0 = '" + row['ITMREF_0'] + "'")
        first_row = cursor2.fetchone()
        if (first_row['TCLCOD_0'] == 'MRKT' or first_row['TCLCOD_0'] == 'ENGCO' or ( first_row['TCLCOD_0'] in ['ENG','ENGSS','ENGCS', 'ITEQP', 'ADMFO', 'LABCH', 'OFF','STAT'] and float(first_row['AVC_0']) <= 5000.0)):
                i = i+ 1
                line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
                product = ET.SubElement(line, 'FLD', {'NAME': 'ITMREF', 'TYPE': 'Char'})
                product.text = row["ITMREF_0"]
                qty = ET.SubElement(line, 'FLD', {'NAME': 'QTYPCU', 'TYPE': 'Decimal'})
                qty.text = str(row["QTYSTU_0"])
                location = ET.SubElement(line, 'FLD', {'NAME': 'LOC', 'TYPE': 'Char'})
                location.text = row["LOC_0"]
                status = ET.SubElement(line, 'FLD', {'NAME': 'STA', 'TYPE': 'Char'})
                status.text = row["STA_0"]
                cost_center = ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'})
                cost_center.text = 'CC013' if first_row['TCLCOD_0'] == 'MRKT' else 'CC016' if first_row['TCLCOD_0'] == 'ITEQP' else 'CC017' if first_row['TCLCOD_0'] == 'ADMFO' or first_row['TCLCOD_0'] == 'OFF' or first_row['TCLCOD_0'] == 'STAT' else 'CC010' if first_row['TCLCOD_0'] == 'LABCH' else 'CC008'
    if i == 0:
        return -1
    
    CContext, client = define_header_json()

    #print(ET.tostring(root_xml))

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName='ZSMO', objectXml=ET.tostring(root_xml))

    result = data.resultXml
    print(data.resultXml)
    result2 = json.loads(str(result))

    return result2['SMO0_1']['VCRNUM']

def zzzcreate_issue_from_reception_in_sage(json_data):
    root_xml = ET.Element("PARAM")
    ET.SubElement(root_xml, 'FLD', {'NAME': 'STOFCY'}).text  = 'M0001'
    ET.SubElement(root_xml, 'FLD', {'NAME': 'VCRDES'}).text  = json_data["PTH0_1"]["PTHNUM"]
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'SMO1_1', 'SIZE': str(len(json_data['PTH1_2']))})

    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    i = 0
    for item in json_data["PTH1_2"]:
        cursor.execute("SELECT i.ITMREF_0, i.TCLCOD_0, m.AVC_0 FROM LIVE.ITMMASTER i INNER JOIN LIVE.ITMMVT m ON m.ITMREF_0 = i.ITMREF_0 WHERE m.STOFCY_0 = 'M0001' AND i.ITMREF_0 = '" + item['ITMREF'] + "'")
        for row in cursor:
            if (row['TCLCOD_0'] == 'MRKT' or row['TCLCOD_0'] == 'ENGCO' or ( row['TCLCOD_0'] in ['ENG','ENGSS','ENGCS', 'ITEQP', 'ADMFO', 'LABCH', 'OFF','STAT'] and float(row['AVC_0']) <= 5000.0)):
                i = i+ 1
                line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
                product = ET.SubElement(line, 'FLD', {'NAME': 'ITMREF', 'TYPE': 'Char'})
                product.text = item["ITMREF"]
                qty = ET.SubElement(line, 'FLD', {'NAME': 'QTYPCU', 'TYPE': 'Decimal'})
                qty.text = str(item["QTYSTU"])
                location = ET.SubElement(line, 'FLD', {'NAME': 'LOC', 'TYPE': 'Char'})
                location.text = item["LOC"]
                status = ET.SubElement(line, 'FLD', {'NAME': 'STA', 'TYPE': 'Char'})
                status.text = item["STA"]
                #line_desc = ET.SubElement(line, 'FLD', {'NAME': 'MVTDES', 'TYPE': 'Char'})
                #line_desc.text = item.description[:30]
                cost_center = ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'})
                cost_center.text = 'CC013' if row['TCLCOD_0'] == 'MRKT' else 'CC016' if row['TCLCOD_0'] == 'ITEQP' else 'CC017' if row['TCLCOD_0'] == 'ADMFO' or row['TCLCOD_0'] == 'OFF' or row['TCLCOD_0'] == 'STAT' else 'CC010' if row['TCLCOD_0'] == 'LABCH' else 'CC008'

                
    
    if i == 0:
        return -1
    
    CContext, client = define_header_json()

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName='ZSMO', objectXml=ET.tostring(root_xml))

    result = data.resultXml
    #xmlInput2 = ET.fromstring(result)
    #code = xmlInput2.findall(".//GRP[@ID='SMO0_1']/FLD[@NAME='VCRNUM']")[0].text
    result2 = json.loads(data.resultXml)

    return result2['SMO0_1']['VCRNUM']


def create_reception_xml_doc(is_doc):
    root_xml = ET.Element("PARAM")
    #root_xml.attrib["action"] = "create"

    ET.SubElement(root_xml, 'FLD', {'NAME': 'STOFCY'}).text  = "M0001" if is_doc.branch == "Kinshasa" else "M0002"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'VCRDES'}).text  = is_doc.name

    nb = frappe.db.count('Material Request Item', {'parent': is_doc.name})
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'SMO1_1', 'SIZE': str(nb)})
    i = 0
    for item in is_doc.items:
        if "_Sage" in item.s_warehouse:
            i = i+ 1
            line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
            product = ET.SubElement(line, 'FLD', {'NAME': 'ITMREF', 'TYPE': 'Char'})
            product.text = item.item_code
            qty = ET.SubElement(line, 'FLD', {'NAME': 'QTYPCU', 'TYPE': 'Decimal'})
            qty.text = str(item.qty)
            location = ET.SubElement(line, 'FLD', {'NAME': 'LOC', 'TYPE': 'Char'})
            location.text = item.s_warehouse.split("_")[0]
            status = ET.SubElement(line, 'FLD', {'NAME': 'STA', 'TYPE': 'Char'})
            status.text = "A"
            line_desc = ET.SubElement(line, 'FLD', {'NAME': 'MVTDES', 'TYPE': 'Char'})
            line_desc.text = item.description[:30]
            cost_center = ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'})
            cost_center.text = item.cost_center.split(" - ")[0]
        

    return root_xml

def create_reception_from_sage(rec_num):
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    cursor.execute('SELECT d.ITMREF_0, d.QTYSTU_0, MIN(s.LOC_0) AS LOC_0, MIN(s.STA_0) AS STA_0 FROM LIVE.PRECEIPTD d INNER JOIN LIVE.STOJOU s ON s.STOFCY_0 = d.PRHFCY_0 AND d.PTHNUM_0 = s.VCRNUM_0 AND d.PTDLIN_0 = s.VCRLIN_0 WHERE PTHNUM_0 = %s GROUP BY d.ITMREF_0, d.QTYSTU_0;', rec_num)
    items = []
    line = {}
    i = 0
    for row in cursor:
        i = i+ 1
        conn2 = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
        cursor2 = conn2.cursor(as_dict=True)
        cursor2.execute("SELECT i.ITMREF_0, i.TCLCOD_0, m.AVC_0 FROM LIVE.ITMMASTER i INNER JOIN LIVE.ITMMVT m ON m.ITMREF_0 = i.ITMREF_0 WHERE m.STOFCY_0 = 'M0001' AND i.ITMREF_0 = '" + row['ITMREF_0'] + "'")
        first_row = cursor2.fetchone()
        code_cost_center = 'CC013' if first_row['TCLCOD_0'] == 'MRKT' else 'CC016' if first_row['TCLCOD_0'] == 'ITEQP' else 'CC017' if first_row['TCLCOD_0'] == 'ADMFO' or first_row['TCLCOD_0'] == 'OFF' or first_row['TCLCOD_0'] == 'STAT' else 'CC010' if first_row['TCLCOD_0'] == 'LABCH' else 'CC008'
        cost_center = frappe.get_value("Cost Center", {"cost_center_number" : code_cost_center}, "name")
        if (first_row['TCLCOD_0'] == 'MRKT' or first_row['TCLCOD_0'] == 'ENGCO' or ( first_row['TCLCOD_0'] in ['ENG','ENGSS','ENGCS', 'ITEQP', 'ADMFO', 'LABCH', 'OFF','STAT'] and float(first_row['AVC_0']) <= 5000.0)):
            line = {
                "t_warehouse": row["LOC_0"] + " - MES",
                "item_code": row["ITMREF_0"],
                "qty": row["QTYSTU_0"],
                "basic_rate": first_row["AVC_0"],
                "branch": 'Kinshasa',
                "cost_center": cost_center,
            }
            items.append(line)

    if i > 0 :
        br_doc = frappe._dict({
            "doctype": "Stock Entry",
            "company": "Marsavco Engg Stock",
            "stock_entry_type": "Material Receipt",
            "items" : items
        })
        doc = frappe.get_doc(br_doc)
        doc.insert()
        doc.submit()
        frappe.db.commit()   
        
        

def zzzcreate_reception_from_sage(data):
    items = []
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)
    line = {}
    i = 0
    for r in data["PTH1_2"]:
        cursor.execute("SELECT i.ITMREF_0, i.TCLCOD_0, m.AVC_0 FROM LIVE.ITMMASTER i INNER JOIN LIVE.ITMMVT m ON m.ITMREF_0 = i.ITMREF_0 WHERE m.STOFCY_0 = 'M0001' AND i.ITMREF_0 = '" + r['ITMREF'] + "'")
        
        for row in cursor:
            i = i+ 1
            code_cost_center = 'CC013' if row['TCLCOD_0'] == 'MRKT' else 'CC016' if row['TCLCOD_0'] == 'ITEQP' else 'CC017' if row['TCLCOD_0'] == 'ADMFO' or row['TCLCOD_0'] == 'OFF' or row['TCLCOD_0'] == 'STAT' else 'CC010' if row['TCLCOD_0'] == 'LABCH' else 'CC008'
            cost_center = frappe.get_value("Cost Center", {"cost_center_number" : code_cost_center}, "name")
            if (row['TCLCOD_0'] == 'MRKT' or row['TCLCOD_0'] == 'ENGCO' or ( row['TCLCOD_0'] in ['ENG','ENGSS','ENGCS', 'ITEQP', 'ADMFO', 'LABCH', 'OFF','STAT'] and float(row['AVC_0']) <= 5000.0)):
                line = {
                    "t_warehouse": r["LOC"] + " - MES",
                    "item_code": r["ITMREF"],
                    "qty": r["QTYSTU"],
                    "basic_rate": row["AVC_0"],
                    "branch": 'Kinshasa',
                    "cost_center": cost_center,
                }
                items.append(line)

                
    
    if i > 0 :
        br_doc = frappe._dict({
            "doctype": "Stock Entry",
            "company": "Marsavco Engg Stock",
            "stock_entry_type": "Material Receipt",
            "items" : items
        })
        doc = frappe.get_doc(br_doc)
        doc.insert()
        doc.submit()
        frappe.db.commit()



def get_today_receipt():
    conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
    cursor = conn.cursor(as_dict=True)

    cursor.execute("SELECT * FROM LIVE.PRECEIPT WHERE RCPDAT_0 = CONVERT(DATE,GETDATE()) AND ZSYNC_0 <> 3")
        
    for row in cursor:
        print(row['PTHNUM_0'])
        code = create_issue_from_reception_in_sage(row['PTHNUM_0'])
        if code != -1 :
            create_reception_from_sage(row['PTHNUM_0'])

        conn3 = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
        up_cursor = conn3.cursor()
        up_cursor.execute('UPDATE LIVE.PRECEIPT SET ZSYNC_0 = 3 WHERE PTHNUM_0 = %s;', row['PTHNUM_0'])
        conn3.commit()

def zzzget_today_receipt():
    today = getdate().strftime('%Y%m%d')
    CContext, client = define_header_json()

    key_xml = [
        {
            'key': 'RCPDAT',
            'value': today
        }
    ]

    with client.settings(strict=False):
        data = client.service.query(callContext=CContext, publicName='ZPTH', objectKeys=key_xml, listSize=10000)

    result = json.loads(data.resultXml)

    for r in result:
        key_xml = [
            {
                'key': 'PTHNUM',
                'value': r['PTHNUM']
            }
        ]
        with client.settings(strict=False):
            data = client.service.read(callContext=CContext, publicName='ZPTH', objectKeys=key_xml)
        
        result2 = json.loads(data.resultXml)
        if result2['PTH0_1']['PRHFCY'] == "M0001":
            code = create_issue_from_reception_in_sage(result2)
            if code != -1 :
                create_reception_from_sage(result2)


        
############################### SALARY WITHDRAWALS ##################################################
def create_salary_xml_doc(pay_doc):
    root_xml = ET.Element("PARAM")
    
    posting_date = getdate()

    emp_name = (pay_doc.employee + " - " + pay_doc.employee_name) if len(pay_doc.employee + " - " + pay_doc.employee_name) <= 30 else (pay_doc.employee + " - " + pay_doc.employee_name)[:30]

    ET.SubElement(root_xml, 'FLD', {'NAME': 'FCY'}).text  = "M0001" if pay_doc.branch == "Kinshasa" else "M0002"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'ACC'}).text  = "42110100"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'BPAINV'}).text  = "1"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'ACCDAT'}).text  = posting_date.strftime("%Y%m%d")
    ET.SubElement(root_xml, 'FLD', {'NAME': 'REF'}).text  = emp_name
    ET.SubElement(root_xml, 'FLD', {'NAME': 'DES'}).text  = pay_doc.pay_period + " | " + pay_doc.type
    ET.SubElement(root_xml, 'FLD', {'NAME': 'BAN'}).text  = pay_doc.cashier
    ET.SubElement(root_xml, 'FLD', {'NAME': 'CUR'}).text  = pay_doc.currency
    ET.SubElement(root_xml, 'FLD', {'NAME': 'AMTCUR'}).text  = str(pay_doc.amount)
    ET.SubElement(root_xml, 'FLD', {'NAME': 'CHQNUM'}).text  = pay_doc.name

    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'PAY1_4', 'SIZE': "1"})
    line = ET.SubElement(lines_xml, 'LIN', {'NUM': "1"})
    code = ET.SubElement(line, 'FLD', {'NAME': 'DENCOD', 'TYPE': 'Char'})
    code.text = "ZAPAY"
    amount = ET.SubElement(line, 'FLD', {'NAME': 'AMTLIN', 'TYPE': 'Decimal'})
    amount.text = str(pay_doc.amount)
    cost_center = ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'})
    cost_center.text = pay_doc.cost_center.split("-")[0].strip()
    employee = ET.SubElement(line, 'FLD', {'NAME': 'CCE5', 'TYPE': 'Char'})
    employee.text = pay_doc.employee
        
    return root_xml


def create_salary_withdrawal(name,public_name='ZPAY'):
    pay_doc = frappe.get_doc("BPM Salary Withdrawals", name)
    xmlInput = create_salary_xml_doc(pay_doc)
    CContext, client = define_header_xml()

    #frappe.msgprint(str(len(xmlInput)))

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName=public_name, objectXml=ET.tostring(xmlInput))

    result = data.resultXml
    xmlInput2 = ET.fromstring(result)
    code = xmlInput2.findall(".//GRP[@ID='PAY0_1']/FLD[@NAME='NUM']")[0].text
    return code

############################### SALES ORDER ##################################################
def create_sales_order_xml_doc(doc):
    root_xml = ET.Element("PARAM")
    ET.SubElement(root_xml, 'FLD', {'NAME': 'SALFCY'}).text  = "M0001" if doc.branch == "Kinshasa" else "M0002"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'SOHTYP'}).text  = "SON" if doc.branch == "Kinshasa" else "SOI"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'BPCORD'}).text  = "CE000001" if doc.mode == "Echantillon" else "CM000029"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'CUSORDREF'}).text  = doc.reference

    nb = frappe.db.count('BPM Sampling Details', {'parent': doc.name})
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '200', 'ID': 'SOH4_1', 'SIZE': str(nb)})
    i = 0
    for item in doc.details:
        i = i+ 1
        line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
        product = ET.SubElement(line, 'FLD', {'NAME': 'ITMREF', 'TYPE': 'Char'})
        product.text = item.item
        qty = ET.SubElement(line, 'FLD', {'NAME': 'QTY', 'TYPE': 'Decimal'})
        qty.text = str(item.qty)
        
    return root_xml


def create_sales_order(name,public_name='ZSOH'):
    doc = frappe.get_doc("BPM Marketing Sampling", name)
    xmlInput = create_sales_order_xml_doc(doc)
    CContext, client = define_header_xml()

    #frappe.throw(str(xmlInput))

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName=public_name, objectXml=ET.tostring(xmlInput))

    result = data.resultXml
    xmlInput2 = ET.fromstring(result)
    code = xmlInput2.findall(".//GRP[@ID='SOH0_1']/FLD[@NAME='SOHNUM']")[0].text
    return code

############################### CREDIT NOTES ##################################################
def create_customer_bp_invoice_doc(doc, types):
    root_xml = ET.Element("PARAM")
    
    ET.SubElement(root_xml, 'FLD', {'NAME': 'FCY'}).text = "M0001" if doc.branch == "Kinshasa" else "M0002"
    ET.SubElement(root_xml, 'FLD', {'NAME': 'SIVTYP'}).text = types
    ET.SubElement(root_xml, 'FLD', {'NAME': 'BPR'}).text = "CE000001" if doc.mode == "Echantillon" else "CM000029"
    #ET.SubElement(root_xml, 'FLD', {'NAME': 'STA', 'MENULAB': 'Posted', 'MENULOCAL' : '2261'}).text = '3'
    
    desc_xml = ET.SubElement(root_xml, 'LST', {'NAME': 'DES', 'SIZE': '3', 'TYPE': "Char"})
    for text in [doc.categorie, doc.reference, doc.description[:30] if doc.description else None]:
        if text:
            ET.SubElement(desc_xml, 'ITM').text = text
            
    ET.SubElement(root_xml, 'FLD', {'NAME': 'ACCDAT'}).text = doc.date.strftime("%Y%m%d")
    ET.SubElement(root_xml, 'FLD', {'NAME': 'PTE'}).text = 'CSH'
    ET.SubElement(root_xml, 'FLD', {'NAME': 'CUR'}).text = doc.devise
    ET.SubElement(root_xml, 'FLD', {'NAME': 'BPRVCR'}).text = doc.name

    dim_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '20', 'ID': 'BIC1_5', 'SIZE': '6'})
    dims = ['CCT', 'PRD', 'ITM', 'BPT', 'EMP', 'VEH']
    for i, die_value in enumerate(dims, start=1):
        dim_line = ET.SubElement(dim_xml, 'LIN', {'NUM': str(i)})
        ET.SubElement(dim_line, 'FLD', {'NAME': 'NUMLIG2', 'TYPE': 'Integer'}).text = str(i)
        ET.SubElement(dim_line, 'FLD', {'NAME': 'DIE', 'TYPE': 'Char'}).text = die_value
        ET.SubElement(dim_line, 'FLD', {'NAME': 'CCE', 'TYPE': 'Char'})
        ET.SubElement(dim_line, 'FLD', {'NAME': 'ZCCE', 'TYPE': 'Char'})

    nb = frappe.db.count('BPM Sampling Details', {'parent': doc.name})
    lines_xml = ET.SubElement(root_xml, 'TAB', {'DIM': '300', 'ID': 'BIC3_1', 'SIZE': str(nb)})
    
    for i, item in enumerate(doc.details, start=1):
        line = ET.SubElement(lines_xml, 'LIN', {'NUM': str(i)})
        ET.SubElement(line, 'FLD', {'NAME': 'ACC1', 'TYPE': 'Char'}).text = doc.account
        ET.SubElement(line, 'FLD', {'NAME': 'AMTNOTLIN', 'TYPE': 'Decimal'}).text = str(item.amount)
        ET.SubElement(line, 'FLD', {'NAME': 'DES', 'TYPE': 'Char'}).text = item.item
        ET.SubElement(line, 'FLD', {'NAME': 'VAT', 'TYPE': 'Char'}).text = "TVAEX"
        ET.SubElement(line, 'FLD', {'NAME': 'CCE1', 'TYPE': 'Char'}).text = get_string_part(doc.cost_center)
        ET.SubElement(line, 'FLD', {'NAME': 'CCE2', 'TYPE': 'Char'}).text = item.marque
        ET.SubElement(line, 'FLD', {'NAME': 'CCE3', 'TYPE': 'Char'}).text = item.type
    #frappe.throw(str((root_xml)))
    return root_xml


def create_credit_note(name, public_name='ZCUINVOICE'):
    doc = frappe.get_doc("BPM Marketing Sampling", name)
    xmlInput = create_customer_bp_invoice_doc(doc, "ZACRN")
    CContext, client = define_header_xml()

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName=public_name, objectXml=ET.tostring(xmlInput))

    # Convert the XML Element to a string
    #frappe.throw(str(len(data)))
    #xml_str = ET.tostring(xmlInput, encoding='unicode')
    #frappe.throw(str(xml_str))

    # Parse the outer XML string
    xml_str = ET.tostring(data._raw_elements[1], encoding='unicode')
    outer_root = etree.fromstring(xml_str)
    # Extract and unescape the embedded XML content
    embedded_xml_string = outer_root.text
    unescaped_xml_string = html.unescape(embedded_xml_string)
    
    xmlInput2 = ET.fromstring(unescaped_xml_string)
    code = xmlInput2.findall(".//GRP[@ID='BIC0_1']/FLD[@NAME='NUM']")[0].text
    return code

def process_sage_response(data):
    # Parse the outer XML string
    xml_str = ET.tostring(data._raw_elements[1], encoding='unicode')
    outer_root = etree.fromstring(xml_str)
    # Extract and unescape the embedded XML content
    embedded_xml_string = outer_root.text
    unescaped_xml_string = html.unescape(embedded_xml_string)
    
    return ET.fromstring(unescaped_xml_string)

