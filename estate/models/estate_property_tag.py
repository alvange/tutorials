from odoo import models, fields, api
from odoo.exceptions import UserError
'''A single leading _underscore is a convention (not enforced) that indicates an attribute or function is intended to be private.
It signals to other developers that it is not meant to be accessed directly, but Py does not prevent access.
A double leading __underscore triggers name mangling, meaning Py internally modifies the attribute name to avoid accidental conflicts in subclasses.
Python renames __name to _ClassName__name.'''

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag" # This is the technical name of the Odoo model.
    _description = "Property Tags" # This is the technical description of the Odoo model.
    _order = "name"

    name = fields.Char(string="Tag", required=True, search=True)
    color = fields.Integer('Color Index') # This should correspond to o_tag_color_X
    
    # SQL constraint to enforce uniqueness. Case-insensitive:
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The Tag must be unique.')
    ]
    '''('unique_tag', 
            'UNIQUE(LOWER(name))', 
            'The Type must be unique (case-insensitive).')'''
    # To enforce c-i uniqueness and send a custom message when a duplicate is detected, you can implement a Py validation inside your model using @api.constrains. This allows Odoo to check for existing values and raise an error with your custom message when needed:
    @api.constrains('name')
    def _check_unique_case_insensitive(self):
        for record in self:
            existing = self.search([('id', '!=', record.id), ('name', '=ilike', record.name)])
            if existing:
                raise UserError("The Tag must be unique (case-insensitive).")

'''A many2many (properties with tags) is a bidirectional multiple relationship: any record on one side can be related to any number of records on the other side.'''