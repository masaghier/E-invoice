import json

import requests

import base64

import ast

import http.client as httplib

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"


    # document_type = fields.Selection([
    #     ('I', 'Invoice'),
    #     ('C', 'Credit note'),
    #     ('D', 'Debit note')
    # ])
    resp = fields.Char()
    uuid = fields.Char('UUID', compute='get_uuid')
    eta_long_id = fields.Char(compute='get_long_id')
    fired = fields.Integer()
    status = fields.Char('Status', compute='get_status')
    error_message = fields.Text('Error message', compute='get_status')

    def get_token(key, secret, version, env_type):
        auth = str(key + ":" + secret)
        message_bytes = auth.encode()
        base64_bytes = base64.b64encode(message_bytes).decode('ascii')
        loginurl = ""
        loginmethod = "/connect/token"
        if env_type == "Pre Production":
            loginurl = "id.preprod.eta.gov.eg" #Identity Service
            #systemAPI = "https://api.preprod.invoicing.eta.gov.eg"
        else:
            loginurl = "id.eta.gov.eg"
            #systemAPI = "https://api.invoicing.eta.gov.eg"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "Authorization": "Basic %s" % base64_bytes
        }
        body = "grant_type=client_credentials"
        conn = httplib.HTTPSConnection(loginurl, timeout=10)
        conn.request("POST", loginmethod, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()
        result = json.loads(data)
        return result.get("access_token")

    def get_state(self, uuid):
        version = self.company_id.invoice_version
        login_url = 'api.preprod.invoicing.eta.gov.eg'
        login_method = f'/api/v1.0/documents/{uuid}/details'
        token = AccountMove.get_token(self.company_id.client_id, self.company_id.client_secret_1,version,"Pre Production")
        headers = {
            "Authorization"   : f"Bearer {token}",
            "Accept"          : "application/json",
            "Accept-Language" : "ar",
            "Content-Type"    : "application/json",
        }
        c = httplib.HTTPSConnection(login_url)
        c.request("GET", login_method, headers=headers)
        res = c.getresponse()
        print(token)
        print("**************")
        print(res)
        r = res.read()
        print("********")
        print(r)
        data = json.loads(r)
        status = data.get('status')
        return status

    #Created by zizo
    def eta_print(self):
        return {'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': '_blank',
                'url': f'https://preprod.invoicing.eta.gov.eg/print/documents/{self.uuid}/share/{self.eta_long_id}'
                }

    def action_send_einvoice(self):
        data = []
        for rec in self:
            total_taxes = 0
            invoicelines = []
            issued_date = rec.invoice_date

            # start edited by zizo
            sum_t1 = 0
            sum_t4 = 0
            for i in self.invoice_line_ids:
                if i.tax_ids:
                    for tax in i.tax_ids:
                        if tax.eta_tax_type == "T1":
                            sum_t1 = sum_t1 + round((i.price_subtotal * tax.amount/100), 5)
                        elif tax.eta_tax_type == "T4":
                            sum_t4 = sum_t4 + round((i.price_subtotal * tax.amount/100), 5)

            tax_totals = [{"taxType": "T1", "amount": sum_t1}, {"taxType": "T4", "amount": sum_t4}]
            # end edited by Zizo

            document_type = ''
            if rec.move_type == 'out_invoice':
                document_type = 'I'
            elif rec.move_type == 'out_refund':
                document_type = 'C'

            for line in rec.invoice_line_ids:
                taxable_items = []
                for tax in line.tax_ids:
                    taxable_items.append({"taxType": tax.eta_tax_type,
                                          "amount": round((line.price_subtotal * tax.amount/100), 5), # round(tax.amount, 5), #edited by zizo
                                          "subType": tax.eta_tax_subtype,
                                          "rate": tax.amount})

                invoicelines.append({
                    "description": line.name,
                    "itemType": line.product_id.item_type ,
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

            data.append({"issuer": {
                "address": {"branchID": rec.company_id.branch_id or "",
                            "country": rec.company_id.country_id.code or "",
                            "governate": rec.company_id.state_id.name or "",
                            "regionCity": rec.company_id.city or "",
                            "street": rec.company_id.street or "",
                            "buildingNumber": "1",
                            "postalCode": rec.company_id.zip or "", "floor": "", "room": "", "landmark": "",
                            "additionalInformation": ""},
                "type": rec.company_id.org_type or "", "id": rec.company_id.vat or "",
                "name": rec.company_id.name or ""},

                "receiver": {
                    "address": {"branchID": rec.partner_id.branch_id or "",
                                "country": rec.partner_id.country_id.code or "",
                                "governate": rec.partner_id.state_id.name or "",
                                "regionCity": rec.partner_id.city or "",
                                "street": rec.partner_id.street or "",
                                "buildingNumber": "1", "postalCode": rec.partner_id.zip or "", "floor": "", "room": "",
                                "landmark": "",
                                "additionalInformation": ""}, "type": rec.partner_id.org_type or "",
                    "id": rec.partner_id.vat or "",
                    "name": rec.partner_id.name or ""},

                "documentType": document_type, "documentTypeVersion": rec.company_id.invoice_version,
                "dateTimeIssued": issued_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "taxpayerActivityCode": rec.company_id.activity_code or "", "internalID": rec.name,
                "purchaseOrderReference": "",
                "purchaseOrderDescription": "", "salesOrderReference": "", "salesOrderDescription": "",
                "proformaInvoiceNumber": "",
                "payment": {"bankName": "", "bankAddress": "", "bankAccountNo": "", "bankAccountIBAN": "",
                            "swiftCode": "",
                            "terms": ""},
                "delivery": {"approach": "", "packaging": "", "dateValidity": "", "exportPort": "",
                             "countryOfOrigin": "",
                             "grossWeight": 0, "netWeight": 0, "terms": ""}, "invoiceLines": invoicelines,
                "totalDiscountAmount": 0, "totalSalesAmount": rec.amount_untaxed, "netAmount": rec.amount_untaxed,
                # "taxTotals": self.amount_by_group or "",
                # {"taxType": "T1", "amount": self.amount_by_group}
                "taxTotals": tax_totals,
                "totalAmount": rec.amount_total, "extraDiscountAmount": 0.0, "totalItemsDiscountAmount": 0})

        jsoned = json.dumps(data)
        print("****JSON sent*****")
        print(jsoned)
        req = requests.post(rec.company_id.signature_api_url, headers={'Content-Type': 'application/json'},
                            data=jsoned, verify=False)
        rec.resp = json.loads(req.text)
        rec.fired = 1
        print("****response****")
        print(rec.resp)

    @api.depends('uuid')
    def get_uuid(self):
        for rec in self:
            if self.fired:
                at = ast.literal_eval(rec.resp)
                if at["acceptedDocuments"]:
                    rec.uuid = at["acceptedDocuments"][0]["uuid"]
                    print(f"*UUID*: {rec.uuid}")
                elif at["rejectedDocuments"]:
                    rec.uuid = ''
            else:
                rec.uuid = ''

    @api.depends('eta_long_id')
    def get_long_id(self):
        for rec in self:
            if self.fired:
                at = ast.literal_eval(rec.resp)
                if at["acceptedDocuments"]:
                    rec.eta_long_id = at["acceptedDocuments"][0]["longId"]
                elif at["rejectedDocuments"]:
                    rec.eta_long_id = ''
            else:
                rec.eta_long_id = ''

    @api.depends('status', 'error_message')
    def get_status(self):
        for rec in self:
            if self.fired:
                at = ast.literal_eval(rec.resp)
                if at["acceptedDocuments"]:
                    #rec.status = AccountMove.get_state(self, self.uuid)
                    rec.status = rec.get_state(rec.uuid)
                    rec.error_message = ''
                elif at["rejectedDocuments"]:
                    rec.status = ''
                    rec.error_message = at["rejectedDocuments"][0]["error"]["details"][0]["message"]
            else:
                rec.status = ''
                rec.error_message = ''

