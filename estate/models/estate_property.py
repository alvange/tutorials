#import sys
#odo = sys.path.append(r'C:\odoo\odoo')  # Path where odoo/__init__.py exists
from datetime import date, datetime, timedelta
import pytz # type: ignore
from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError
'''A single leading _underscore is a convention (not enforced) that indicates an attribute or function is intended to be private.
It signals to other developers that it is not meant to be accessed directly (from the presentation tier, only from the business tier) but Py does not prevent access.
A double leading __underscore triggers name mangling, meaning Py internally modifies the attribute name to avoid accidental conflicts in subclasses.
Python renames __name to _ClassName__name.'''

class EstateProperty(models.Model): # inherits from Model which provides create(), read(), write() and unlink().
    _name = "estate.property" # This is the tech name of the Odoo model (metadata: module.model).
    _description = "Real Estate Property" # This is the technical description of the Odoo model (metadata).
    _order = "id desc"

    name = fields.Char(string="Name", required=True, search=True, default="Fill in a name or title")
    description = fields.Text(string="Description")

    user_id = fields.Many2one('res.users', string='Salesman', index=True, default=lambda self: self.env.user) 
    #This sets the default value for the field to the current logged-in user. Self in lambda self is specific to the EstateProperty instance. 
    # Self in self.env.user uses the same instance but accesses the environment layer where env exists as a gateway which provides access to the broader components, including user, database cursor, registries, and more.
    #Each record of your model can be linked to one record in the 'res.users' model (which is the built-in Users model in Odoo). This is similar to a foreign key in a relational DB. So, this field is a foreign key to the res.users model. 
    buyer_id = fields.Many2one('res.partner', string='Buyer', copy=False)
    
    # A link between models. Type table is a Lookup table and property_type_id is the foreign-key. The term lookup table is sometimes used for tables like Countries, which hold a fixed set of reference data. A lookup table participates in a many-to-one relationship.
    property_type_id = fields.Many2one("estate.property.type", store=True, string="Property Type") # many properties to 1 type.
    #property_offer_ids = fields.one2many(comodel_name="estate.property.offer", inverse_name='property_id')
    property_offer_ids = fields.One2many("estate.property.offer", "property_id") # 1 property to many offers.
    property_tag_ids = fields.Many2many("estate.property.tag", string="Tags") 
    #tag_colors_data = fields.Json(string='Tag Color Data', compute='_compute_tag_colors_data', store=False)

    '''@api.depends('property_tag_ids')
    def _compute_tag_colors_data(self):
        for record in self:
            tags = record.property_tag_ids.read(['id', 'display_name', 'color'])
            record.tag_colors_data = tags
            record.tag_colors_data = [
                {'id': tag.id, 'display_name': tag.display_name, 'color': tag.color}
                for tag in record.property_tag_ids
            ]'''
    
    # OJO you need to convert this into a Helper Function:
    local_timezone = pytz.timezone('America/Mexico_City')  # Replace with your timezone
    # Convert UTC now to local date
    local_today = datetime.now(local_timezone).date()
    print("Local date:", local_today)
    print("timedelta(days=90):", local_today + timedelta(days=90))
    
    postcode = fields.Char(string="Postcode", search=True)
    date_availability = fields.Date(
        string="Date Availability", 
        copy=False, 
        # default=lambda self: date.today() + timedelta(days=90), # Default to 3 months from today
        default=lambda self: self.local_today + timedelta(days=90), # Default to 3 months from today
        help='Default to 3 months from today'
        )
    
    # OJO search=True functionality is inherent to fields in Odoo's ORM, so you don't need to explicitly specify it.
    expected_price = fields.Float(string="Expected Price", required=True, search=True)
    # SQL constraint at the model level
    selling_price = fields.Float(string="Selling Price", readonly=True, copy=False)
    _sql_constraints = [
    ('check_expected_price', 'CHECK(expected_price > 0)', 'The expected price of a property should be positive.'),
    ('check_selling_price', 'CHECK(selling_price >= 0)', 'The selling price of a property should be positive.')
    ]

    bedrooms = fields.Integer(string="Bedrooms", default=2, search=True)
    living_area = fields.Integer(string="Living Area (sqm)", search=True)
    facades = fields.Integer(string="Facades", search=True)
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Garden")
    
    # Think of onchange as a helpful guide for users interacting with the system, rather than a reliable mechanism for enforcing rules or processing business logic. They help dynamically update or suggest default values for fields based on other input by the user. You're essentially implementing business UI logic rather than core business logic. 
    @api.onchange("garden")
    def _onchange_garden(self): # self represents the record in the form view. Decorate it with onchange() to specify which field it is triggered by. Any change you make on self will be reflected on the form:
        print('EXE _onchange_garden:', self.garden)
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = ""
            # This is a dictionary used for user messages, not best practice:
            '''return {'warning': {
                'title': _("Warning"),
                'message': _('You have set garden_area & garden_orientation to none values.')}}'''

    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West')
    ], string="Garden Orientation")
    # active is a reserved field for a specific behaviour. The active field is used to auto filter out inactive records.
    active = fields.Boolean("Active", default=True) # Add Active field as inactive (false)  string="Active",
    # State reflects the stage of the property in its lifecycle. Current internal condition, changes dynamically (ex: traffic light system), its usage is for internal systems or logic. State is a reserved field as well. A state field is used in combination with a states attribute in the view to display buttons conditionally.
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled')
    ], string="State", required=True, copy=False, default='new')
    
    

    # The value of totalArea is computed on the fly each time it's accessed (when you open a form or list view).
    totalArea = fields.Float(compute="_compute_totalArea") # You cannot directly set its value because it's derived from the computation.
    @api.depends("living_area", "garden_area")
    def _compute_totalArea(self): # it passes in one or more estate.property records that need their totalArea field computed. 
        print('# of records for _compute_totalArea(self):', len(self))
        self.totalArea = self.living_area + self.garden_area # Note that we don't loop on self, this is because the method is only triggered in a form view, where self is always a single record.
    
    # Dichotomy: Since CF's are not stored, it's not possible to search on a computed field unless a search method is defined. 
    # store=True means the value will be saved in the DB. It can be used in search filters and reports, which is important for performance and usability. 
    best_offerPrice = fields.Float(compute="_compute_best_price", store=True) 
    @api.depends("property_offer_ids.price")
    def _compute_best_price(self):# it passes in one or more estate.property records that need their best_offerPrice field computed. 
        print('# of records for _compute_best_price(self):', len(self.property_offer_ids))
        #for record in self:
            #record.best_offerPrice = max(record.property_offer_ids.mapped('price'), default=0.0)
            # Use the mapped() method to extract the prices from the related offers
        self.best_offerPrice = max(self.property_offer_ids.mapped('price'), default=0.0) # No need for looping using mapped.

    def action_sold_prop(self):
        for record in self:
            print('record.state', record.state)
            if record.state == 'cancelled':
                # Using UserError ensures proper error feedback in line with Odoo's framework.
                raise UserError(_('Cancelled properties cannot be sold.'))
            #  The write method respects Odoo's ORM mechanisms, ensuring workflows, computed fields, or other dependent logic are triggered properly.
            #record.state = "sold"
            record.write({'state': 'sold'})

            '''Create invoice. Create an empty account.move in the override of the action_sold method:
            the partner_id is taken from the current estate.property
            the move_type should correspond to a “Customer Invoice”
            Tips: to create an object, use self.env[model_name].create(values), where values is a dict. 
            'invoice_line_ids': This is a list that holds multiple invoice line items.
            (0, 0, {...}): This tuple follows Odoo’s record creation format. The (0, 0, {...}) structure means a new record is being created without an existing ID. 
            (1, 45, { # Updating an existing invoice line with ID 45. 1 This indicates that an existing record will be modified
            '''
            print('self.buyer_id:',self.buyer_id)
            
            move_values = {
                "name": "Test",
                'partner_id':  self.buyer_id.id,  # Ensure it's an integer ID, #property.partner_id.id, 
                'move_type': 'out_invoice',  # Corresponds to a Customer Invoice
                'invoice_date': self.local_today,  # Sets the invoice date to today's date
                'invoice_line_ids': [
                    (0, 0, {  # First invoice line - 6% of selling price
                        'name': 'Commission Fee',
                        'quantity': 1,
                        'price_unit': self.selling_price * 0.06,
                        'account_id': self.env['account.account'].search([('account_type', '=', 'income')], limit=1).id,
                    }),
                    (0, 0, {  # Second invoice line - Administrative Fee
                        'name': 'Administrative Fees',
                        'quantity': 1,
                        'price_unit': 100.00,
                        'account_id': self.env['account.account'].search([('account_type', '=', 'income')], limit=1).id,
                    })
                ],
            }
            self.env['account.move'].create(move_values) # move_values is a dictionary/object
            
            default_journal = self.env['account.journal'].search([
                ('type', '=', 'sale'),  # Journal type for customer invoices
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            print('Default_journal:',default_journal, ' Company_id:',self.env.company.id)

            #invoice_vals_list = []
            #ref_invoice_vals = None
            #invoice_vals_list.append(ref_invoice_vals)
            #moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
            #return moves
        return True
    
    def action_cancel_prop(self):
        for record in self:
            if record.state == 'sold':
                raise UserError(_('Sold properties cannot be cancelled.'))
            #record.state = "cancelled"
            record.write({'state': 'cancelled'})
        return True
    
    ''' I used this in the frontend: <list string="Real Estate Properties" decoration-success="state == 'offer_received'"
    offer_received = fields.Boolean(string="Offer Received", compute="_compute_offer_received", store=True)
    @api.depends('property_offer_ids')
    def _compute_offer_received(self): # to identify if an offer was received:
        for record in self:
            record.offer_received = bool(record.property_offer_ids)
            if record.offer_received: # and  property.state not in ['offer_accepted', 'sold', 'cancelled']:
                record.state = 'offer_received'''
   
    # It's also important to note that even though we can directly override the unlink() method, you will almost always want to write a new method with the decorator ondelete() instead. Methods marked with this decorator will be called during unlink() and avoids some issues that can occur during uninstalling the model’s module when unlink() is directly overridden. 
    @api.ondelete(at_uninstall=False)
    def _ondelete_check_state(self): # remember that self can be a recordset with more than one record (for exe:bulk delete).
        for record in self:
            if record.state not in ['new', 'cancelled']:
                raise UserError("You cannot delete a property unless its state is 'New' or 'Cancelled'")
            
    '''<button name="action_print_to_console"
                                type="object"
                                string="Print Variable"
                                class="btn-primary"/>'''
    def action_print_to_console(self):
        for record in self:
            print("Field Value:", record.property_type_id.name)  # This prints to the server console

"""
# Without mapped you'll need to use a loop like this:
for record in self:
        max_price = 0.0
        for offer in record.property_offer_ids:
            if offer.price > max_price:
                max_price = offer.price
        record.best_offerPrice = max_price

class TotalAreaComputed(models.Model):
    _inherit "estate_property" # you need to inherit to be able to access living_area and garden_area
    _name = "totalArea.computed"
    totalArea = fields.Float(compute="_compute_totalArea")
    @api.depends("living_area", "garden_area")
    def _compute_totalArea(self):
        for record in self: record.totalArea = record.living_area + record.garden_area """

'''
Many2one: The relationship between Props and Types is many-to-one because many properties can belong to the same type. By convention, many2one fields have the _id suffix. Accessing the data in the partner can then be easily done with: print(my_test_object.partner_id.name)

Many2many: The relationship between Props and Tags is indeed many-to-many, as one property can belong to multiple tags and one tag can apply to multiple properties. It's a bidirectional multiple relationship: any record on one side can be related to any number of records on the other side. By convention, many2many fields have the _ids suffix. tax_ids = fields.Many2many("account.tax", string="Taxes") this means that several taxes can be added to our test model. It behaves as a list of records, meaning that accessing the data must be done in a loop: for tax in my_test_object.tax_ids: print(tax.name)

One2many: An offer applies to one property, but the same property can have many offers. The concept of many2one appears once again. However, in this case we want to display the list of offers for a given property so we will use the one2many concept.
A one2many is the inverse of a many2one. For ex, we defined on our test model a link to the res.partner model thanks to the field partner_id. We can define the inverse relation, i.e. the list of test models linked to our partner:
test_ids = fields.One2many("test_model", "partner_id", string="Tests") The 1st parameter is called the comodel and the 2nd parameter is the field we want to inverse. By convention, one2many fields have the _ids suffix.
Because a One2many is a virtual relationship, there must be a Many2one field defined in the comodel.
One2many relationships are not only useful for structuring data but also play a significant role in reporting. Here's how they are leveraged:Data Structuring for Reports, Custom Views in Reports, Filtering and Aggregation, Excel and Pivot Table Exports.

lambda self: defines an anonymous function (a function without a name) that takes one parameter, self. In this context, self refers to the current instance of the model (estate.property), and it's typically used to access model data or methods.
In this specific case, the lambda function does not actually use self to reference anything within the model. It's just a handy way to calculate and return the default value dynamically. Its sole purpose is to calculate the default date as date.today() + timedelta(days=90).

ODOO's Environment vars:
In Odoo, env provides access to DB models.
 a = env['inheritance.0'].create({'name': 'A'})    b = env['inheritance.1'].create({'name': 'B'})
 a.call() # calls the method from inheritance.0    b.call() # calls the method from inheritance.1 which overrides the base call method.
 # inheritance.0 is the tech name of the model. 'name' is a field defined in this case within the base model.

Odoo provides 3 different mechanisms to extend models in a modular way:
https://www.odoo.com/documentation/15.0/es/developer/reference/backend/orm.html#reference-orm-inheritance 

'''