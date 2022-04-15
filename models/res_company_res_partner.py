from odoo import models, fields
from pathlib import Path
import json

path1 = Path(__file__).parent / "jsonData/activity codes.json"
with path1.open() as activityCode:
    activity = json.load(activityCode)

for i in range(len(activity)):
    activity[i] = (activity[i]["code"], activity[i]["code"] + " " + activity[i]["Desc_ar"])


class ResCompany(models.Model):
    _inherit = 'res.company'

    branch_id = fields.Char('Branch Id')
    org_type = fields.Selection([('B', 'Business'),
                                 ('F', 'Foreign'),
                                 ('P', 'Person')], string='Type')
    activity_code = fields.Selection(activity)
    client_id = fields.Char('Client id')
    client_secret_1 = fields.Char('Client secret 1')
    client_secret_2 = fields.Char('Client secret 2')
    invoice_version = fields.Selection([
        ('1.0', '1.0'),
        ('0.9', '0.9')
    ], required=True)
    signature_api_url = fields.Char('Signature API URL')
    environment = fields.Selection([
        ('production', 'Production'),
        ('preproduction', 'Preproduction')
    ])


class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_id = fields.Char('Branch Id')
    org_type = fields.Selection([('B', 'Business'),
                                 ('F', 'Foreign'),
                                 ('P', 'Person')], string='Type')
