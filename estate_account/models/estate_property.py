''' Any time we interact with another module, we need to keep in mind the modularity. If we intend to sell our app to real estate agencies, some may want the invoicing feature but others may not want it.
What matters is that in estate_account, you're using _inherit = 'estate.property' to extend the existing model, not redefining it.'''
from odoo import models

class EstateProperty(models.Model):
    _inherit = 'estate.property'

    #def action_sold(self): 
    def action_sold_prop(self):
        print("DEBUG: estate_account - action_sold override called")
        # Or use breakpoint()
        # import pdb; pdb.set_trace()
        return super().action_sold_prop()
