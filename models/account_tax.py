from odoo import models, fields
import json
from pathlib import Path

path1 = Path(__file__).parent / "jsonData/taxTypes.json"
with path1.open() as taxType:
    tax_type = json.load(taxType)

for i in range(len(tax_type)):
    tax_type[i] = (tax_type[i]["Code"], tax_type[i]["Code"] + " " + tax_type[i]["Desc_ar"])

path2 = Path(__file__).parent / "jsonData/taxSubType.json"
with path2.open() as taxSubtype:
    tax_sub_type = json.load(taxSubtype)

for i in range(len(tax_sub_type)):
    tax_sub_type[i] = (tax_sub_type[i]["Code"], tax_sub_type[i]["Code"] + " " + tax_sub_type[i]["Desc_ar"])


class AccountTax(models.Model):
    _inherit = 'account.tax'

    eta_tax_type = fields.Selection(tax_type, string='ETA tax type')

    eta_tax_subtype = fields.Selection(
        tax_sub_type, string='ETA tax subtype'
    )
