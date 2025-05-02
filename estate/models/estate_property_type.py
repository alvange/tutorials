#import sys
#odo = sys.path.append(r'C:\odoo\odoo')  # Path where odoo/__init__.py exists
from odoo import models, fields, api
from odoo.exceptions import UserError
'''A single leading _underscore is a convention (not enforced) that indicates an attribute or function is intended to be private.
It signals to other developers that it is not meant to be accessed directly, but Py does not prevent access.
A double leading __underscore triggers name mangling, meaning Py internally modifies the attribute name to avoid accidental conflicts in subclasses.
Python renames __name to _ClassName__name.'''

class EstatePropertyType(models.Model):
    # If you're using Odoo’s ORM, you can remove the index by executing SQL inside your module:
    def init(self):
        try:
            #self._cr.execute("""
            #    CREATE UNIQUE INDEX IF NOT EXISTS unique_type_ci
            #    ON estate_property_type (LOWER(name));
            #""")
            self._cr.execute("""
            DROP INDEX IF EXISTS unique_type_ci;
            """)
        except Exception as e:
            raise UserError(f"Failed to DROP unique index for property type: {str(e)}")

    _name = "estate.property.type" # This is the technical name of the Odoo model.
    _description = "Property Type" # This is the technical description of the Odoo model.
    # Your model should be ordered by the sequence when using the widget handle to turn the field into a drag-and-drop handle.
    _order =  "sequence" # "name" # You can also define the order in the view: <list default_order="date desc">
    # default=1: This sets the default value of the field to 1 when a new record is created—unless another value is provided.
    sequence = fields.Integer('Sequence', default=1, help="Used to order types auto or manually using sequence.")

    name = fields.Char(string="Type", required=True, search=True)
    '''name = fields.Selection([
        ('house', 'House'), ('department', 'Department'), ('building', 'Building'), ('hostel', 'Hostel')
    ], string="Type", required=True, default='house', search=True)'''

    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties') # 1 type to many properties. property_type_id = Many2one (many properties to 1 type)

    '''@api.depends('property_ids') 
    def _compute_property_ids_count(self): #??
        for record in self:
            record.property_ids_count = len(record.property_ids)'''

    # SQL constraint to enforce uniqueness. Case-insensitive:
    '''_sql_constraints = [ PostgreSQL does not allow using a function like LOWER(name) directly in a UNIQUE constraint.
        ('unique_type', 'UNIQUE(LOWER(name))', 'The Type must be unique (case-insensitive).')
    ]'''
    # To enforce c-i uniqueness and send a custom message when a duplicate is detected, you can implement a Py validation inside your model using @api.constrains. This allows Odoo to check for existing values and raise an error with your custom message when needed:
    @api.constrains('name')
    def _check_unique_case_insensitive(self):
        for record in self:
            existing = self.search([('id', '!=', record.id), ('name', '=ilike', record.name)])
            if existing:
                raise UserError("The Type must be unique (case-insensitive).")

    # offer_ids = all offers related to properties for a given type:
    offer_ids = fields.One2many(
        'estate.property.offer',  # related model
        'property_type_id',       # field on estate.property.offer that links back to estate.property.type (Many2one)
        string="Offers"
    )

    # if we don't store the data the _compute_offer_count doesn't work?? Without store=True, the framework doesn’t know when or where to trigger the computation outside of runtime access. Additionally, if store=True is set, Odoo knows to include this field when views are rendered or when filters are applied, making the system more efficient and predictable.
    offer_count = fields.Integer(
        string="Offer Count",
        compute="_compute_offer_count",
        store=True, 
    )

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            print('_compute_offer_count:', len(record.offer_ids))
            record.offer_count = len(record.offer_ids)

    
    



'''
A many2one (property with type) is a simple link to another object (lookup table). The term lookup table is sometimes used for tables like Countries, which hold a fixed set of reference data. A lookup table participates in a many-to-one relationship.

lambda self: defines an anonymous function (a function without a name) that takes one parameter, self. In this context, self refers to the current instance of the model (estate.property), and it's typically used to access model data or methods.
In this specific case, the lambda function does not actually use self to reference anything within the model. It's just a handy way to calculate and return the default value dynamically. Its sole purpose is to calculate the default date as date.today() + timedelta(days=90).
'''