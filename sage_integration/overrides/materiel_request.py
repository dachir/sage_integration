import frappe
from erpnext.stock.doctype.material_request.material_request import MaterialRequest
from sage_integration.utils.soap_ws import create_pr
import pymssql
import html2text

class CustomMaterialRequest(MaterialRequest):

    def before_submit(self):
        super().before_submit()
        if self.material_request_type == "Purchase": 
            self.sage_pr = create_pr(self.name)
    
    def on_submit(self):
        super().on_submit()
        if self.material_request_type == "Purchase": 
            #self.sage_pr = create_pr(self.name)
            self.traitement_details()
        #elif self.material_request_type == "Material Issue":
            #self.sage_pr = create_issue(self.name)


    def traitement_details(self):
        conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
        cursor = conn.cursor(as_dict=True)
        up_conn = pymssql.connect("172.16.0.40:49954", "erpnext", "Xn5uFLyR", "dc7x3v12")
        up_cursor = up_conn.cursor()

        cursor.execute('SELECT ITMREF_0 FROM LIVE.PREQUISD WHERE PSHNUM_0 = %s', self.sage_pr)
        for row in cursor:
            data =frappe.db.sql(
                """
                SELECT description
                FROM `tabMaterial Request Item`
                WHERE parent = %s and item_code = %s
                """, (self.name, row["ITMREF_0"]), as_dict = 1
            )
            if len(data) > 0:
                h = html2text.HTML2Text()
                up_cursor.execute('UPDATE LIVE.PREQUISD SET ZTEXT_0 = %s WHERE ITMREF_0 = %s;', (h.handle(data[0].description[:250]),row['ITMREF_0']))
                up_conn.commit()
            
        up_conn.close()
        conn.close()



            




