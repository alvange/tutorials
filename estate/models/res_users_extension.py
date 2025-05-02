'''By convention, each inherited model is defined in its own Python file. In our example, it would be models/inherited_model.py.
Odoo provides three different mechanisms to extend models in a modular way: Inheritance, extension & delegation
Extension:
When using _inherit but leaving out _name, the new model replaces the existing one, essentially extending it in-place. This is useful to add new fields or methods to existing models (created in other modules), or to customize or reconfigure them (to change their default sort order) '''

#from dataclasses import fields
#from odoo.addons.account import models
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)  # Creates a logger instance

class ResUsers(models.Model):
    '''_inherit extends the existing model, does not redefine it.'''
    _inherit = 'res.users' 

    property_ids = fields.One2many(
        'estate.property', 
        'user_id', 
        string='Properties Seller', 
        domain=[('state', 'not in', ["offer_accepted", "sold", "cancelled"])]
        )
    
    # This ensures the logger statement runs only when the model is initialized, which allows self.env to exist.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'user_id' in self.env['estate.property']._fields:
           #_logger.info("user_id is present in estate.property!")
            pass
        else:
            #_logger.error("user_id is missing from estate.property!")
           pass
        #_logger.info(f"Fields in estate.property: {self.env['estate.property']._fields.keys()}")
        


'''class ResUsers(models.Model):
    _inherit = 'res.users' # Classical inheritance: extending res.users model. Using _inherit but leaving out _name (Extension - ). 

    property_ids = fields.One2many(
        'estate_property', # Related model
        'user_id' , # Inverse field (salesperson in estate.property)
        string='Properties Seller', 
        domain=[('state', 'not in', ["offer_accepted", "sold", "cancelled"])] # Domain to filter only available properties
    ) '''

