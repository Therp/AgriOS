# -*- coding: utf-8 -*-
{
    'name': "Kobo Toolbox Integration - Agrios",
    'summary': """Kobo Toolbox Extention For Agrios Application""",
    'author': "Advance Insight",
    'website': "https://advanceinsight.dev",
    'category': 'Services/AIODKIntegration',
    'version': '18.0.1.0.1',
    'license': 'Other proprietary',
    'depends': [
        'ai_kobo_integration',
        'agrios',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/kobo_asset_actions.xml',
        'views/action_utils_models.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}