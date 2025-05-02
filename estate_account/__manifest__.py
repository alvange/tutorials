# __manifest__.py
#Menus are typically loaded last, as they rely on the views and models being in place to function correctly.
{
    'name': 'Estate Account',
    'version': '1.0',
    'category': 'Real Estate',
    'summary': 'Extension for Estate: Accounting Integration',
    'description': 'An shell for integrating Estate with Accounting for invoice creation.',
    'depends': ['estate', 'account'],
    'data': [],
    'installable': True,
    'application': False,
}

'''OJO The data section should only list XML or CSV files for records — never .py files.
'application': False: This indicates that the module is not considered a standalone app. Instead, it is likely an add-on or extension meant to complement existing features rather than being an independent app in Odoo’s module structure.
When 'application': True, the module is treated as a main app, typically appearing in the Apps menu within Odoo’s interface. Setting it to False generally means it's more of a backend utility, extra functionality, or a submodule rather than a full-fledged app. 
Dependencies in Odoo work only forward—meaning estate_account depends on account, but account does not depend on estate_account.
When you uninstall estate_account, Odoo will simply remove it but will not touch its dependencies (estate or account). These will remain installed unless you manually remove them.
So, in terms of software architecture:
    Highly decoupled: Implies modules have minimal dependencies and can evolve independently.
    In Odoo, only some standalone apps qualify as highly decoupled.
    Most extensions or non-standalone modules are not highly decoupled—they are by design tightly coupled to what they extend.'''