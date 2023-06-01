import frappe
import zeep
import requests
import xml.etree.ElementTree as ET
from frappe.utils import getdate
import json
import pymssql

def create_xml_doc(pr_doc):
    root_xml = ET.Element("PARAM")
    #root_xml.attrib["action"] = "create"

    branch = frappe.db.get_list("Material Request Item", filters={'parent': pr_doc.name}, fields=["Max(branch) as branch"])[0].branch
    ET.SubElement(root_xml, 'FLD', {'NAME': 'PSHFCY'}).text  = "M0001" if branch == "Kinshasa" else "M0002"

    if frappe.session.user == 'Administrator':
        requester = 'ADMIN'
    else:
        requester = frappe.get_value("Employee",{"user_id":frappe.session.user},"sage_code")
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

    return root_xml



def create_pr(name):
    pr_doc = frappe.get_doc("Material Request", name)
    
    xmlInput = create_xml_doc(pr_doc)
    CContext, client = define_header_xml()

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName='ZPSR', objectXml=ET.tostring(xmlInput))

    result = data.resultXml
    xmlInput2 = ET.fromstring(result)
    #test = ET.tostring(xmlInput)
    #frappe.msgprint(test.decode())
    code = xmlInput2.findall(".//GRP[@ID='PSH0_1']/FLD[@NAME='PSHNUM']")[0].text

    return code


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

def create_issue(name):
    is_doc = frappe.get_doc("Stock Entry", name)
    xmlInput = create_issue_xml_doc(is_doc)
    CContext, client = define_header_xml()

    with client.settings(strict=False):
        data = client.service.save(callContext=CContext, publicName='ZSMO', objectXml=ET.tostring(xmlInput))

    result = data.resultXml
    xmlInput2 = ET.fromstring(result)
    code = xmlInput2.findall(".//GRP[@ID='SMO0_1']/FLD[@NAME='VCRNUM']")[0].text

    return code

def create_issue_from_reception_in_sage(json_data):
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
            if row['TCLCOD_0'] == 'MRKT' or row['TCLCOD_0'] == 'ENGCO' or ( row['TCLCOD_0'] in ['ENG','ENGSS','ENGCS', 'ITEQP', 'ADMFO', 'LABCH', 'OFF','STAT'] and float(row['AVC_0']) <= 5000.0):
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
    xmlInput2 = ET.fromstring(result)
    code = xmlInput2.findall(".//GRP[@ID='SMO0_1']/FLD[@NAME='VCRNUM']")[0].text

    return code


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

def create_reception_from_sage(data):
    items = []
    for r in data["PTH1_2"]:
        line = {
            "t.warehouse": r["LOC"],
            "item_code": r["ITMREF"],
            "qty": r["QTYSTU"],
        }
    br_doc = frappe._dict({
        "company": "Marsavco Engg Stock",
        "stock_entry_type": "Material Receipt",
    })

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

def get_today_receipt():
    today = getdate().strftime('%Y%m%d')
    CContext, client = define_header_json()

    key_xml = [
        {
            'key': 'RCPDAT',
            'value': today
        }
    ]

    with client.settings(strict=False):
        data = client.service.query(callContext=CContext, publicName='ZPTH', objectKeys=key_xml, listSize=1000)

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
        if result2['PRHFCY'] == "M0001":
            cost = create_issue_from_reception_in_sage(result2)
            if cost != -1 :
                create_reception_from_sage(result2,cost)

        
       
        


    