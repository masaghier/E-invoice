from odoo import models, fields
from pathlib import Path
import json

path1 = Path(__file__).parent / "jsonData/Unit Types.json"
with path1.open() as unitTypes:
    unit_types = json.load(unitTypes)

for i in range(len(unit_types)):
    unit_types[i] = (unit_types[i]["code"], unit_types[i]["code"] + " " + unit_types[i]["desc_en"])

class Uom(models.Model):
    _inherit = 'uom.uom'

    unit_type = fields.Selection(unit_types, string='Unit type')
