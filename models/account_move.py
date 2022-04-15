import json

import requests

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    # document_type = fields.Selection([
    #     ('I', 'Invoice'),
    #     ('C', 'Credit note'),
    #     ('D', 'Debit note')
    # ])
    uuid = fields.Char('UUID', compute='action_send_einvoice')
    resp = ''

    @api.depends('uuid')
    def action_send_einvoice(self):
        total_taxes = 0
        invoicelines = []
        issued_date = self.invoice_date

############# start edited by zizo
        sum_t1 = 0
        sum_t4 = 0
        for rec in self.invoice_line_ids:
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    if tax.eta_tax_type == "T1":
                        sum_t1 = sum_t1 + (rec.price_subtotal * tax.amount/100)
                    elif tax.eta_tax_type == "T4":
                        sum_t4 = sum_t4 + (rec.price_subtotal * tax.amount/100)

        tax_totals = []
        tax_totals.append({"taxType": "T1", "amount": sum_t1})
        tax_totals.append({"taxType": "T4", "amount": sum_t4})
############# end edited by zizo

        document_type = ''
        if self.move_type == 'out_invoice':
            document_type = 'I'
        elif self.move_type == 'out_refund':
            document_type = 'C'

        for line in self.invoice_line_ids:
            taxable_items = []
            for tax in line.tax_ids:
                taxable_items.append({"taxType": tax.eta_tax_type,
                                      "amount": (line.price_subtotal * tax.amount/100), # round(tax.amount, 5), #edited by zizo
                                      "subType": tax.eta_tax_subtype,
                                      "rate": tax.amount})

            invoicelines.append({
                "description": line.name,
                "itemType": line.product_id.item_type,
                "itemCode": line.product_id.item_code,
                "unitType": line.product_uom_id.unit_type,
                "quantity": line.quantity,
                "internalCode": line.product_id.default_code,
                "salesTotal": line.price_unit * line.quantity,
                "total": round(line.price_subtotal * 1.14, 5), #edited by zizo
                "valueDifference": 0,
                "totalTaxableFees": 0,
                "netTotal": line.price_subtotal, #edited by zizo
                "itemsDiscount": 0.0, #edited by zizo
                "unitValue": {
                    "currencySold": "EGP",
                    "amountEGP": line.price_unit,
                    "amountSold": 0,
                    "currencyExchangeRate": 0
                },
                "discount": {
                    "rate": 0.0,
                    "amount": line.discount #edited by zizo
                },
                "taxableItems": taxable_items #edited by zizo
            })

        data = {"issuer": {
            "address": {"branchID": self.company_id.branch_id or "",
                        "country": self.company_id.country_id.code or "",
                        "governate": self.company_id.state_id.name or "",
                        "regionCity": self.company_id.city or "",
                        "street": self.company_id.street or "",
                        "buildingNumber": "1",
                        "postalCode": self.company_id.zip or "", "floor": "", "room": "", "landmark": "",
                        "additionalInformation": ""},
            "type": self.company_id.org_type or "", "id": self.company_id.vat or "",
            "name": self.company_id.name or ""},

            "receiver": {
                "address": {"branchID": self.partner_id.branch_id or "",
                            "country": self.partner_id.country_id.code or "",
                            "governate": self.partner_id.state_id.name or "",
                            "regionCity": self.partner_id.city or "",
                            "street": self.partner_id.street or "",
                            "buildingNumber": "1", "postalCode": self.partner_id.zip or "", "floor": "", "room": "",
                            "landmark": "",
                            "additionalInformation": ""}, "type": self.partner_id.org_type or "",
                "id": self.partner_id.vat or "",
                "name": self.partner_id.name or ""},

            "documentType": document_type, "documentTypeVersion": self.company_id.invoice_version,
            "dateTimeIssued": issued_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "taxpayerActivityCode": self.company_id.activity_code or "", "internalID": self.name,
            "purchaseOrderReference": "",
            "purchaseOrderDescription": "", "salesOrderReference": "", "salesOrderDescription": "",
            "proformaInvoiceNumber": "",
            "payment": {"bankName": "", "bankAddress": "", "bankAccountNo": "", "bankAccountIBAN": "",
                        "swiftCode": "",
                        "terms": ""},
            "delivery": {"approach": "", "packaging": "", "dateValidity": "", "exportPort": "",
                         "countryOfOrigin": "",
                         "grossWeight": 0, "netWeight": 0, "terms": ""}, "invoiceLines": invoicelines,
            "totalDiscountAmount": 0, "totalSalesAmount": self.amount_untaxed, "netAmount": self.amount_untaxed,
            # "taxTotals": self.amount_by_group or "",
            # {"taxType": "T1", "amount": self.amount_by_group}
            "taxTotals": tax_totals,
            "totalAmount": self.amount_total, "extraDiscountAmount": 0.0, "totalItemsDiscountAmount": 0}

        jsoned = json.dumps(data)
        print("****JSON sent*****")
        print(jsoned)
        req = requests.post(self.company_id.signature_api_url, headers={'Content-Type': 'application/json'},
                            data=jsoned, verify=False)
        resp = json.loads(req.text)
        print("****response****")
        print(resp)

        for rec in self:
            if resp:
                rec.uuid = resp["acceptedDocuments"][0]["uuid"]
            else:
                rec.uuid = ''

    def print_ata(self):
