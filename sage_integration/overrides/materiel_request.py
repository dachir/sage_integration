import frappe
from erpnext.stock.doctype.material_request.material_request import MaterialRequest
from sage_integration.utils.soap_ws import create_pr

class CustomMaterialRequest(MaterialRequest):
    
    def on_submit(self):
        super().on_submit()
        if self.material_request_type == "Purchase": 
            self.sage_pr = create_pr(self.name)
        #elif self.material_request_type == "Material Issue":
            #self.sage_pr = create_issue(self.name)



