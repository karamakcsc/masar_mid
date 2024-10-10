# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt


import json
from collections import defaultdict

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.workflow import get_workflow_name, is_transition_condition_satisfied
from frappe.utils import (
	flt,
	get_link_to_form,
	getdate,
)
from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.controllers.accounts_controller import (set_order_defaults , 
                                                     validate_and_delete_children , 
                                                     update_last_purchase_rate)


class VariationOrder(Document):
    def validate(self):
        if len(self.current_items) > 0:
            self.fetch_po_warehouse()
    
    def on_submit(self):
        self.update_items_po()

    @frappe.whitelist()
    def fetch_child_items(self):
        self.current_items = []
        source_doc = frappe.get_doc("Purchase Order", self.purchase_order)
        
        for row in source_doc.items:
            self.append("current_items", {
				"item_code": row.item_code,
				"item_name": row.item_name,
				"item_group": row.item_group,
				"schedule_date": row.schedule_date,
				"qty": row.qty,
				"rate": row.rate,
				"amount": row.amount,
				"warehouse": row.warehouse,
				"expense_account": row.expense_account,
				"project": row.project,
				"budget_element": row.budget_element,
				"cost_center": row.cost_center,
				"po_description": row.custom_po_description,
				"description": row.description
			})
        self.total_qty = source_doc.total_qty
        self.total = source_doc.total
        
        self.update_items = []
        for item in source_doc.items:
            self.append("update_items", {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"item_group": item.item_group,
				"schedule_date": item.schedule_date,
				"qty": item.qty,
				"rate": item.rate,
				"amount": item.amount,
				"warehouse": item.warehouse,
                "docname": item.name,
				"expense_account": item.expense_account,
				"project": item.project,
				"budget_element": item.budget_element,
				"cost_center": item.cost_center,
				"po_description": item.custom_po_description,
				"description": item.description
			})
        
        return True
    
    def fetch_po_warehouse(self):
        warehouse = frappe.db.sql("SELECT DISTINCT warehouse FROM `tabPurchase Order Item` WHERE parent = %s",
                                  (self.purchase_order), as_dict = True)
        # frappe.throw(str(warehouse[0]['warehouse']))
        
        if warehouse and warehouse[0] and warehouse[0]['warehouse']:
            for row in self.update_items:
                row.warehouse = warehouse[0]['warehouse']
                
    
    def update_items_po(self):
        trans_items = list()
        for row in self.update_items:
            data = frappe._dict({
                'item_code' : row.item_code , 
                'schedule_date': row.schedule_date, 
                'qty': row.qty,
                'rate':row.rate,
                'amount' : row.amount,
                'warehouse' : row.warehouse , 
                'expense_account' : row.expense_account, 
                'project' : row.project, 
                'budget_element' : row.budget_element, 
                'cost_center': row.cost_center,
				'description': row.po_description
            })
            if row.docname:
                data['docname'] =  row.docname
                data['name'] =  row.docname
            trans_items.append(data)
        update_child_qty_rate(parent_doctype = 'Purchase Order' , 
                              trans_items = json.dumps(trans_items) , 
                              parent_doctype_name = self.purchase_order ,
                              child_docname="items")

@frappe.whitelist()
def update_child_qty_rate(parent_doctype, trans_items, parent_doctype_name, child_docname="items"):
	def check_doc_permissions(doc, perm_type="create"):
		try:
			doc.check_permission(perm_type)
		except frappe.PermissionError:
			actions = {"create": "add", "write": "update"}

			frappe.throw(
				_("You do not have permissions to {} items in a {}.").format(
					actions[perm_type], parent_doctype
				),
				title=_("Insufficient Permissions"),
			)

	def validate_workflow_conditions(doc):
		workflow = get_workflow_name(doc.doctype)
		if not workflow:
			return

		workflow_doc = frappe.get_doc("Workflow", workflow)
		current_state = doc.get(workflow_doc.workflow_state_field)
		roles = frappe.get_roles()

		transitions = []
		for transition in workflow_doc.transitions:
			if transition.next_state == current_state and transition.allowed in roles:
				if not is_transition_condition_satisfied(transition, doc):
					continue
				transitions.append(transition.as_dict())

		if not transitions:
			frappe.throw(
				_("You are not allowed to update as per the conditions set in {} Workflow.").format(
					get_link_to_form("Workflow", workflow)
				),
				title=_("Insufficient Permissions"),
			)

	def get_new_child_item(item_row):
		child_doctype = "Sales Order Item" if parent_doctype == "Sales Order" else "Purchase Order Item"
		return set_order_defaults(parent_doctype, parent_doctype_name, child_doctype, child_docname, item_row)

	def validate_quantity(child_item, new_data):
		if not flt(new_data.get("qty")):
			frappe.throw(
				_("Row #{0}: Quantity for Item {1} cannot be zero.").format(
					new_data.get("idx"), frappe.bold(new_data.get("item_code"))
				),
				title=_("Invalid Qty"),
			)

		if parent_doctype == "Sales Order" and flt(new_data.get("qty")) < flt(child_item.delivered_qty):
			frappe.throw(_("Cannot set quantity less than delivered quantity"))

		if parent_doctype == "Purchase Order" and flt(new_data.get("qty")) < flt(child_item.received_qty):
			frappe.throw(_("Cannot set quantity less than received quantity"))

	def should_update_supplied_items(doc) -> bool:
		"""Subcontracted PO can allow following changes *after submit*:

		1. Change rate of subcontracting - regardless of other changes.
		2. Change qty and/or add new items and/or remove items
		        Exception: Transfer/Consumption is already made, qty change not allowed.
		"""

		supplied_items_processed = any(
			item.supplied_qty or item.consumed_qty or item.returned_qty for item in doc.supplied_items
		)

		update_supplied_items = any_qty_changed or items_added_or_removed or any_conversion_factor_changed
		if update_supplied_items and supplied_items_processed:
			frappe.throw(_("Item qty can not be updated as raw materials are already processed."))

		return update_supplied_items

	def validate_fg_item_for_subcontracting(new_data, is_new):
		if is_new:
			if not new_data.get("fg_item"):
				frappe.throw(
					_("Finished Good Item is not specified for service item {0}").format(
						new_data["item_code"]
					)
				)
			else:
				is_sub_contracted_item, default_bom = frappe.db.get_value(
					"Item", new_data["fg_item"], ["is_sub_contracted_item", "default_bom"]
				)

				if not is_sub_contracted_item:
					frappe.throw(
						_("Finished Good Item {0} must be a sub-contracted item").format(new_data["fg_item"])
					)
				elif not default_bom:
					frappe.throw(_("Default BOM not found for FG Item {0}").format(new_data["fg_item"]))

		if not new_data.get("fg_item_qty"):
			frappe.throw(_("Finished Good Item {0} Qty can not be zero").format(new_data["fg_item"]))

	data = json.loads(trans_items)

	any_qty_changed = False  # updated to true if any item's qty changes
	items_added_or_removed = False  # updated to true if any new item is added or removed
	any_conversion_factor_changed = False

	sales_doctypes = ["Sales Order", "Sales Invoice", "Delivery Note", "Quotation"]
	parent = frappe.get_doc(parent_doctype, parent_doctype_name)

	check_doc_permissions(parent, "write")
	_removed_items = validate_and_delete_children(parent, data)
	items_added_or_removed |= _removed_items

	for d in data:
		new_child_flag = False

		if not d.get("item_code"):
			# ignore empty rows
			continue

		if not d.get("docname"):
			new_child_flag = True
			items_added_or_removed = True
			check_doc_permissions(parent, "create")
			child_item = get_new_child_item(d)
		else:
			check_doc_permissions(parent, "write")
			child_item = frappe.get_doc(parent_doctype + " Item", d.get("docname"))

			prev_rate, new_rate = flt(child_item.get("rate")), flt(d.get("rate"))
			prev_qty, new_qty = flt(child_item.get("qty")), flt(d.get("qty"))
			prev_fg_qty, new_fg_qty = flt(child_item.get("fg_item_qty")), flt(d.get("fg_item_qty"))
			prev_con_fac, new_con_fac = (
				flt(child_item.get("conversion_factor")),
				flt(d.get("conversion_factor")),
			)
			prev_uom, new_uom = child_item.get("uom"), d.get("uom")

			if parent_doctype == "Sales Order":
				prev_date, new_date = child_item.get("delivery_date"), d.get("delivery_date")
			elif parent_doctype == "Purchase Order":
				prev_date, new_date = child_item.get("schedule_date"), d.get("schedule_date")

			rate_unchanged = prev_rate == new_rate
			qty_unchanged = prev_qty == new_qty
			fg_qty_unchanged = prev_fg_qty == new_fg_qty
			uom_unchanged = prev_uom == new_uom
			conversion_factor_unchanged = prev_con_fac == new_con_fac
			
			any_conversion_factor_changed |= not conversion_factor_unchanged
			date_unchanged = (
				prev_date == getdate(new_date) if prev_date and new_date else False
			)  # in case of delivery note etc
			if (
				rate_unchanged
				and qty_unchanged
				and fg_qty_unchanged
				and conversion_factor_unchanged
				and uom_unchanged
				and date_unchanged
			):
				continue

		validate_quantity(child_item, d)
		if flt(child_item.get("qty")) != flt(d.get("qty")):
			any_qty_changed = True

		if (
			parent.doctype == "Purchase Order"
			and parent.is_subcontracted
			and not parent.is_old_subcontracting_flow
		):
			validate_fg_item_for_subcontracting(d, new_child_flag)
			child_item.fg_item_qty = flt(d["fg_item_qty"])

			if new_child_flag:
				child_item.fg_item = d["fg_item"]

		child_item.qty = flt(d.get("qty"))
		rate_precision = child_item.precision("rate") or 2
		conv_fac_precision = child_item.precision("conversion_factor") or 2
		qty_precision = child_item.precision("qty") or 2
		child_item.project = d.get("project")
		child_item.cost_center = d.get("cost_center")
		child_item.budget_element = d.get("budget_element")
		child_item.expense_account = d.get("expense_account")
		child_item.warehouse = d.get("warehouse")
		child_item.custom_po_description = d.get("description")
		# Amount cannot be lesser than billed amount, except for negative amounts
		row_rate = flt(d.get("rate"), rate_precision)
		amount_below_billed_amt = flt(child_item.billed_amt, rate_precision) > flt(
			row_rate * flt(d.get("qty"), qty_precision), rate_precision
		)
		if amount_below_billed_amt and row_rate > 0.0:
			frappe.throw(
				_("Row #{0}: Cannot set Rate if amount is greater than billed amount for Item {1}.").format(
					child_item.idx, child_item.item_code
				)
			)
		else:
			child_item.rate = row_rate

		if d.get("conversion_factor"):
			if child_item.stock_uom == child_item.uom:
				child_item.conversion_factor = 1
			else:
				child_item.conversion_factor = flt(d.get("conversion_factor"), conv_fac_precision)

		if d.get("uom"):
			child_item.uom = d.get("uom")
			conversion_factor = flt(
				get_conversion_factor(child_item.item_code, child_item.uom).get("conversion_factor")
			)
			child_item.conversion_factor = (
				flt(d.get("conversion_factor"), conv_fac_precision) or conversion_factor
			)

		if d.get("delivery_date") and parent_doctype == "Sales Order":
			child_item.delivery_date = d.get("delivery_date")

		if d.get("schedule_date") and parent_doctype == "Purchase Order":
			child_item.schedule_date = d.get("schedule_date")

		if flt(child_item.price_list_rate):
			if flt(child_item.rate) > flt(child_item.price_list_rate):
				#  if rate is greater than price_list_rate, set margin
				# # or set discount
				child_item.discount_percentage = 0

				if parent_doctype in sales_doctypes:
					child_item.margin_type = "Amount"
					child_item.margin_rate_or_amount = flt(
						child_item.rate - child_item.price_list_rate,
						child_item.precision("margin_rate_or_amount"),
					)
					child_item.rate_with_margin = child_item.rate
			else:
				child_item.discount_percentage = flt(
					(1 - flt(child_item.rate) / flt(child_item.price_list_rate)) * 100.0,
					child_item.precision("discount_percentage"),
				)
				child_item.discount_amount = flt(child_item.price_list_rate) - flt(child_item.rate)

				if parent_doctype in sales_doctypes:
					child_item.margin_type = ""
					child_item.margin_rate_or_amount = 0
					child_item.rate_with_margin = 0

		child_item.flags.ignore_validate_update_after_submit = True
		if new_child_flag:
			parent.load_from_db()
			child_item.idx = len(parent.items) + 1
			child_item.insert()
		else:
			child_item.save()

	parent.reload()
	parent.flags.ignore_validate_update_after_submit = True
	parent.set_qty_as_per_stock_uom()
	parent.calculate_taxes_and_totals()
	parent.set_total_in_words()
	if parent_doctype == "Sales Order":
		make_packing_list(parent)
		parent.set_gross_profit()
	frappe.get_doc("Authorization Control").validate_approving_authority(
		parent.doctype, parent.company, parent.base_grand_total
	)

	parent.set_payment_schedule()
	if parent_doctype == "Purchase Order":
		parent.validate_minimum_order_qty()
		parent.validate_budget()
		if parent.is_against_so():
			parent.update_status_updater()
	else:
		parent.check_credit_limit()

	# reset index of child table
	for idx, row in enumerate(parent.get(child_docname), start=1):
		row.idx = idx

	parent.save()

	if parent_doctype == "Purchase Order":
		update_last_purchase_rate(parent, is_submit=1)

		if any_qty_changed or items_added_or_removed or any_conversion_factor_changed:
			parent.update_prevdoc_status()

		parent.update_requested_qty()
		parent.update_ordered_qty()
		parent.update_ordered_and_reserved_qty()
		parent.update_receiving_percentage()

		if parent.is_subcontracted:
			if parent.is_old_subcontracting_flow:
				if should_update_supplied_items(parent):
					parent.update_reserved_qty_for_subcontract()
					parent.create_raw_materials_supplied()
				parent.save()
			else:
				if not parent.can_update_items():
					frappe.throw(
						_(
							"Items cannot be updated as Subcontracting Order is created against the Purchase Order {0}."
						).format(frappe.bold(parent.name))
					)
	else:  # Sales Order
		parent.validate_warehouse()
		parent.update_reserved_qty()
		parent.update_project()
		parent.update_prevdoc_status("submit")
		parent.update_delivery_status()

	parent.reload()
	validate_workflow_conditions(parent)

	parent.update_blanket_order()
	parent.update_billing_percentage()
	parent.set_status()

	# Cancel and Recreate Stock Reservation Entries.
	if parent_doctype == "Sales Order":
		from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
			cancel_stock_reservation_entries,
			has_reserved_stock,
		)

		if has_reserved_stock(parent.doctype, parent.name):
			cancel_stock_reservation_entries(parent.doctype, parent.name)

			if parent.per_picked == 0:
				parent.create_stock_reservation_entries()
        
        