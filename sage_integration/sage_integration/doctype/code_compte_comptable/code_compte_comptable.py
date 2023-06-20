# Copyright (c) 2023, Richard and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CodeCompteComptable(Document):
	pass

def get_account(code):
	account = frappe.db.sql(
		"""
			SELECT name
			FROM tabAccount
			Where account_number = %s
		""",(code), as_dict = 1
			 )
	return account[0].name
