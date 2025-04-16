# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	return columns(), data(filters)


def data(filters):
    conditions = " 1=1 "
    if filters.get("item_code"):
        conditions += f" AND tsabb.item_code = '{filters.get('item_code')}'"
        
    if filters.get("purchase_receipt"):
        conditions += f" AND tsabb.voucher_no = '{filters.get('purchase_receipt')}'"
        
    if filters.get("warehouse"):
        conditions += f" AND tsabb.warehouse = '{filters.get('warehouse')}'"
        
    from_date, to_date = filters.get("from_date"), filters.get("to_date")
    if from_date and to_date:
        conditions += f" AND tsabb.creation BETWEEN '{from_date}' AND '{to_date}'"
    sql = frappe.db.sql(f"""
			SELECT 
   				tsabb.name AS `Serial and Batch Bundle No.`, 
       			tsabb.item_code AS `Item Code`, 
          		tsabb.item_name AS `Item Name`, 
            	tsabb.total_qty AS `Total Qty`, 
             	tsabb.avg_rate AS `Avg Rate`, 
              	tsabb.total_amount AS `Total Amount`,
				tsabb.voucher_no AS `Purchase Receipt No.`,
               	tpr.set_warehouse AS `Warehouse`,
                tsabb.warehouse AS `Serial and Batch Warehouse`,
                tsabb.posting_date AS `Posting Date`
			FROM `tabSerial and Batch Bundle` tsabb 
			INNER JOIN `tabPurchase Receipt` tpr ON tsabb.voucher_no = tpr.name 
			WHERE {conditions} AND tsabb.docstatus = 1 AND tsabb.voucher_type = 'Purchase Receipt'
	""")
    
    return sql
 
 
def columns():
	return [
		_("Serial and Batch Bundle No") + ":Link/Serial and Batch Bundle:200",
		_("Item Code") + ":Link/Item:200",
		_("Item Name") + "::200",
		_("Total Qty") + ":Float:150",
		_("Avg Rate") + ":Currency:150",
		_("Total Amount") + ":Currency:150",
		_("Purchase Receipt No") + ":Link/Purchase Receipt:200",
		_("Warehouse") + ":Link/Warehouse:200",
		_("Serial and Batch Warehouse") + ":Link/Warehouse:200",
		_("Posting Date") + ":Date:150",
	]