# __manifest__.py
#Menus are typically loaded last, as they rely on the views and models being in place to function correctly.
{
    'name': 'Real Estate',        # Name of your module. It's the human-readable name of the module. 
    'depends': ['base'],          # Framework dependency (required). Ensure 'estate' is listed here for the res_users_extension],
    'category': 'Sales',
    'author': "Drumer",
    'description': "Manages real estate properties.",
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
        'views/res_users_extension_views.xml',

        #'views/estate_type_property_views.xml',
        #'views/estate_actions.xml',
        #'views/estate_type_menus.xml',
    ],
    'installable': True,
    'application': True,  # the module appears when the “Apps” filter is on.
    'license': 'LGPL-3',
}
#data': [ OJO The data section should only list XML or CSV files for records — never .py files.
#        'security/ir.model.access.csv',
#        'views/estate_property_views.xml',  
#        'views/estate_menus.xml', 