from datetime import date, datetime, timedelta
import pytz # type: ignore
#from venv import logger
from odoo import api, fields, models, api
from odoo import _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

'''A single leading _underscore is a convention (not enforced) that indicates an attribute or function is intended to be private.
It signals to other developers that it is not meant to be accessed directly, but Py does not prevent access.
A double leading __underscore triggers name mangling, meaning Py internally modifies the attribute name to avoid accidental conflicts in subclasses.
Python renames __name to _ClassName__name.'''

class EstatePropertyOffer(models.Model):

    _name = "estate.property.offer" # This is the technical name of the Odoo model.
    _description = "Property offers" # This is the technical description of the Odoo model.
    _order = "price desc"

    price = fields.Float(string="Price")
    # This sql_constraints validation helps maintain data integrity when inserting rows programatically:
    sql_constraints = [
        ('check_price', 'CHECK(price > 0)', # if the check is false the message is shown.
         'The offer price for a property should be positive.')
    ]
    # OJO I added this additional validation to validate directly within the Offer form to catch errors before sending data to the DB:
    @api.onchange("price")
    def _checkPrice(self):
        if self.price < 0:
            raise UserError(_('The offer price for a property should be positive.'))
        
    # Status indicates whether an offer has been approved or rejected. External description or label. Changes less frequently. For communication and tracking (Pending, Shipped, Delivered). Status codes like 200 OK, 404 Not Found. These statuses describe the result of an HTTP request. A state field is used in combination with a states attribute in the view to display buttons conditionally.
    status = fields.Selection([  
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], string="Status", copy=False) # OJO I think the status is optional until the offer has been analyze required=True
    
    partner_id = fields.Many2one('res.partner', required=True)
    property_id = fields.Many2one('estate.property', required=True) # Many offers to one property. This field is hidden from the form because the property_id shouldn't change. 
    
    # OJO you need to convert this into a Helper Function:
    local_timezone = pytz.timezone('America/Mexico_City')  # Replace with your timezone
    # Convert UTC now to local date
    local_today = datetime.now(local_timezone).date()
    print("Local date:", local_today)

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(
        compute="_compute_deadline", 
        inverse="_inverse_deadline",
        #default=lambda self: date.today() + timedelta(days=7), # Default to 7 days from today
        default=lambda self: self.local_today + timedelta(days=7), # Default to 7 days from today
        ) 
    @api.depends("validity", "create_date")
    def _compute_deadline(self): # it passes in one or more estate.property.offer records that need their date_deadline field computed. 
        for record in self: # record points to one instance of the estate_property_offer table's records
            #print('record.property_id:', record.property_id)
            #print('# of records for _compute_deadline(self.property_id):', len(self.property_id), ' (self):', len(self))
            if record.create_date:
                #print('FOUND record.create_date EDITING:')
                #print('record.price:', record.price, ' record.validity:', record.validity, ' record.create_date:', record.create_date)
                local_create_date = self.convertServerTZToLocal(record.create_date)
                #if int(record.property_id) == 1:
                    #print('Server_create_date:', record.create_date)
                record.date_deadline = local_create_date + timedelta(days=record.validity)
            else: 
                #print('NEWID Record so record.create_date is empty')
                #record.date_deadline = date.today() + timedelta(days=record.validity)
                record.date_deadline = self.local_today + timedelta(days=record.validity) # local_today makes sure it's the local timezone
            #print('local_create_date:', local_create_date,  'record.date_deadline:', record.date_deadline)
    
    def _inverse_deadline(self): 
        # It updates the validity field when the date_deadline changes. A compute method sets the field while an inverse method sets the field’s dependencies. Note that the inverse method is called when saving the record, while the compute method is called at each change of its dependencies. 
        for record in self: 
            if record.create_date and record.date_deadline:
                #print('# of records for _Inverse_deadline(self.property_id):', len(self.property_id), ' (self):', len(self))
                #print('local_create_date__inverse BEFORE:', record.create_date)
                local_create_date = self.convertServerTZToLocal(record.create_date)
                #if int(record.property_id) == 1:
                #print('local_create_date__inverse AFTER:', local_create_date)
                # Convert both to datetime.date for consistency to allow the subtraction operation between these two dates:
                #create_date = record.create_date.date() if isinstance(record.create_date, datetime) else record.create_date
                create_date = local_create_date.date() if isinstance(record.create_date, datetime) else local_create_date
                date_deadline = record.date_deadline if isinstance(record.date_deadline, date) else record.date_deadline.date()
                #print('date_deadline:', date_deadline, ' create_date:', create_date)
                record.validity = (date_deadline - create_date).days
                #print('record.property_id__inverse:', record.property_id, ' record.validity:', record.validity)
    
    def convertServerTZToLocal(self, create_date):
         # Convert `create_date` from UTC to your local timezone
        local_create_date = create_date.astimezone(self.local_timezone)
        return local_create_date
    
    def action_accept_offer(self):
        #print('# of records for action_accept_offer(self):', len(self))
        #countAccepted = 0
        for record in self:
            found = self.getAccepted()
            
            if found:
                #record.write({'status': 'refused'})
                raise UserError(_('An offer has already been accepted.'))
        validOffer = self._check_percent_offer()
        if not validOffer:
            raise UserError("The selling price must be at least 90% of the expected price.")

        record.write({'status': 'accepted'}) #record.state = "cancelled" 
        print('Record.price:', record.price)
        print('Buyer_id:', int(self.partner_id))
        #record.write({self.property_id.selling_price: float(record.price)})
        # OJO The line above is problematic because write expects a dictionary where the keys are field names as strings, e.g., {'selling_price': value}. But in your code, self.property_id.selling_price evaluates to a value, not a string field name.
        self.property_id.write({'selling_price': float(record.price)})
        self.property_id.write({'buyer_id': int(self.partner_id)})
        self.property_id.write({'state': "offer_accepted"})

        return True
    
    def action_refuse_offer(self):
        #print('# of records for action_refuse_offer(self):', len(self))
        for record in self:
            #if record.status == 'accepted':
            #    record.property_id.write({'state': "new"})
            record.write({'status': 'refused'}) #record.state = "refused"
        return True
    
    @api.model
    def getAccepted(self):
        # Fetch all records of this model
        all_records = self.search([('property_id', '=', int(self.property_id))])
        print('# of records for loop_method(all_records):', len(all_records))

        for record in all_records:# Do something with each record
            #logger.info("Record ID: %s, Name: %s", record.id, record.status) # use this for production
            print("Record ID: %s, status: %s", record.id, record.status)
            if record.status == "accepted":
                return True
        return False

    # check that the offer is 90% or greater than the expected price. Always use the float_compare() and float_is_zero() methods from odoo.tools.float_utils when working with floats!:
    @api.constrains('price')
    def _check_percent_offer(self):
        for record in self:
            sellingPrice = record.price #v1
            expectedPrice = self.property_id.expected_price
            offerPercentage = (sellingPrice * 100) / expectedPrice
            #NinetyPercPrice = (expectedPrice * OfferPercentage) / 100
            print('OfferPercentage:', offerPercentage)
            ninetyPerc = 90

            # Using a precision of 2 digits
            result = float_compare(offerPercentage, ninetyPerc, precision_digits=2)
            if result == 0:
                print("Values are considered equal")
            elif result > 0:
                print("OfferPercentage is greater than ninetyPerc")
            else:
                print("OfferPercentage is less than ninetyPerc")
                return False
        return True
    
    # The exercise introduces the concept of Related fields. Thanks to this field, an offer will be linked to a property type when it’s created. You can add the field to the list view of offers to make sure it works. <field name="property_type_id"/>
    #partner_id = fields.Many2one("res.partner", string="Partner")
    #description = fields.Char(related="partner_id.name")
    property_type_id = fields.Many2one( # one type to many offers for a specific property via property_id.property_type_id
        'estate.property.type',
        string='Property Type',
        related='property_id.property_type_id', # property_id (links back to estate.property) = Many2one Many offers to one property for the given property_type_id (property_type_id field is used for the One2many in the estate.property.type)
        store=True,
    )
    
    # The following logic assumes that the state field and the list of restricted states are defined correctly in the estate.property model. If you're bypassing Odoo's ORM (or if your script bypasses the ORM) and directly inserting data into PostgreSQL (via raw SQL queries), this check won’t apply. The validation logic only works when records are created through Odoo's ORM.    
    #If you're concerned about ensuring these restrictions at the DB level, you may want to implement constraints in PostgreSQL to complement the app-level checks. For ex, a trigger could enforce similar rules within the DB.
    @api.model # create(): Needs @api.model write(), unlink(): Work on existing records  should use @api.multi (Odoo 12 and below) or no decorator in newer versions (Odoo 13+ where @api.multi is implicit). read(), search(), etc.: Depending on how they're used, they might need @api.model, @api.model_create_multi, or no decorator.
    # when creating a new offer update the state to offer_received.
    def create(self, vals):  # vals is accesing the values/fields of the current model. Here Create method is overriding.
         # Do some business logic, modify vals... vals['name'] = 'Nacho'  #  Correct way to set a key in a dictionary
        property_id = vals.get('property_id') # Use parentheses with .get() & Use brackets vals[] to set a value
        print("EXE CREATE property_id:", int(property_id))

        if property_id:
            # To instantiate an estate.property object, use self.env[model_name].browse(value)
            property = self.env['estate.property'].browse( int(property_id) )
            if property.state in ['offer_accepted', 'sold', 'cancelled']:
                raise UserError(
                    _("You cannot create offers for properties that are in 'Offer Accepted', 'Sold', or 'Cancelled' state.")
                )
            
        # Check the new offer must be higher than the highest offer:
        # Fetch existing offers if any. search(domain, limit, offset, order) offset=desplazamiento/compensación
        existing_offers = self.search([('property_id', '=', int(property_id))], 
            order='price desc', 
            limit=1)
        print('existing_offers:', len(existing_offers))

        if existing_offers:
            # Find the highest existing offer amount
            max_offer_amount = max(existing_offers.mapped('price'))
            print('vals.get(price):', vals.get('price'), ' max_offer_amount:', max_offer_amount)
            if vals.get('price') <= max_offer_amount:
                raise UserError(_("The offer must be higher than {}").format(max_offer_amount))
        # Set the property state to 'Offer Received'
        print("CREATE offer.property_id:", int(property_id), ' property_id.state:', property.state)
        property.state = 'offer_received'
        
        #offer = super().create(vals)
        # Ensure property_id is present and update state only if not already 'offer_accepted'
        '''if offer.property_id and offer.property_id.state != 'offer_accepted':
            print("CREATE offer.property_id:", offer.property_id, ' property_id.state:',offer.property_id.state)
            offer.property_id.state = 'offer_received'''
         
         # Then call super to execute the parent method and proceed with creating the offer:
        return super().create(vals)
    
    '''class EstatePropertyOffer(models.Model):
        _name = "estate.property.offer"
        _inherit = ["estate.property.offer"]  # optional, if you're extending an existing model
        def create(self, vals):
            '''
    
    

    

    
'''
PENDING:
1. Can you add a new offer if an offer has been accepted? (intent):  once an offer has been accepted, you typically cannot add a new offer by default. This is by design, to reflect realistic business logic—once an offer is accepted, the property is considered reserved or under negotiation. So change the state to offer_received (in the property) while there is no offer accepted.
2. How do you detect in Odoo when a new record is added in the estate.property.offer module? (intent): 
a) Overriding the create Method. b) Using Automated (Server) Actions 




A one2many (properties with offers) is the inverse of a many2one. For ex: in the props with types many2one relationship you want to list all the props that have the type of Department. one-2-many and many-2-one are two sides of the same coin.
Props  Type is a many-2-one (many props share a type)
Type  Props is the inverse: one-2-many (one type has many props)
We don’t need an action or a menu for all models. Some models are intended to be accessed only through another model. This is the case in our exercise: an offer is always accessed through a property.
Despite the fact that the property_id field is required, we didn't include it in the views. How does Odoo know which property our offer is linked to? Well that’s part of the magic of using the Odoo framework: sometimes things are defined implicitly. When we create a record through a one2many field, the corresponding many2one is populated automatically for convenience.

By convention, compute methods are private, meaning that they cannot be called from the presentation tier, only from the business tier (see Chapter 1: Architecture Overview). Private methods have a name starting with an underscore _.
Ex: class MyController(http.Controller):
        @http.route('/force_compute', auth='user')
        def force_compute(self, order_id):
            order = http.request.env['my.order'].browse(order_id)
            total = order._compute_total()  # ❌ Wrong! Direct call to compute method
            return f"The total is {total}"
            return f"The total is {order.total}"  #  Let Odoo ORM handle the compute
If you need to force recomputation, use: (But again, this should be done in the model or service logic, not directly in the controller:)
order._recompute_fields(['total'])  # Still not common in presentation tier, better in business logic
It is also worth noting that a computed field can depend on another computed field. The ORM is smart enough to correctly recompute all the dependencies in the right order… but sometimes at the cost of degraded performance.In general performance must always be kept in mind when defining computed fields.
There is no strict rule for the use of computed fields and onchanges.

In many cases, both computed fields and onchanges may be used to achieve the same result. Always prefer computed fields since they are also triggered outside of the context of a form view. Never ever use an onchange to add business logic to your model. This is a very bad idea since onchanges are not auto triggered when creating a record programmatically; they are only triggered in the form view. Using computed fields ensures that no matter how or where records are created or updated—whether through the UI, programmatic operations, or external integrations—the business logic remains consistent and reliable.
An example of the wrong practice to use Onchange for business logic and then creating a record programmatically:
@api.onchange('price')
    def _onchange_price(self):
        if self.price > 100: self.discount = 10 else: self.discount = 0

# Programmatically creating a product record
new_product = env['product.product'].create({
    'price': 120
})
# The discount field will not be updated correctly
print(new_product.discount)  # Output: 0
Provide an ex of when a developer may programmatically create a product record instead of using the UI/form for the same purpose (intent):Scenario: Data Import or Bulk Creation

The usual pitfall of computed fields and onchanges is trying to be “too smart” by adding too much logic. This can have the opposite result of what was expected: the end user is confused from all the automation.

Computed fields tend to be easier to debug: such a field is set by a given method, so it’s easy to track when the value is set. Onchanges, on the other hand, may be confusing: it's very difficult to know the extent of an onchange. Since several onchange methods may set the same fields, it easily becomes difficult to track where a value is coming from.

When using stored computed fields, pay close attention to the dependencies. When computed fields depend on other computed fields, changing a value can trigger a large number of recomputations. This leads to poor performance.

record.write({'create_date': new_date}) By using the ORM methods like write(), Odoo will detect the change, trigger the dependency mechanism, and recompute related computed fields.
Manual edits in the DB are risky and should be approached with caution, as they might bypass other important Odoo processes such as validations, triggers, or workflows. 

.'''