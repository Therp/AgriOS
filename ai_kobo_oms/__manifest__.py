# -*- coding: utf-8 -*-
{
    'name': "Kobo Toolbox Integration - OMS",
    'summary': """Kobo Toolbox Extention For OMS Application""",
    'author': "Advance Insight",
    'website': "https://advanceinsight.dev",
    'category': 'Services/AIODKIntegration',
    'version': '18.0.1.0.0',
    'license': 'Other proprietary',
    'depends': [
        'ai_kobo_integration',
        'ai_oms',
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