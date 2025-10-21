# Copyright 2025 Advance Insight
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Kobo Toolbox Integration - Agrios",
    "summary": """Kobo Toolbox Extention For Agrios Application""",
    "author": "Advance Insight",
    "website": "https://github.com/OCA/web",
    "category": "Services/AIODKIntegration",
    "version": "18.0.1.0.5",
    "license": "LGPL-3",
    "depends": [
        "ai_kobo_integration",
        "agrios",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/kobo_asset_actions.xml",
        "views/action_utils_models.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
