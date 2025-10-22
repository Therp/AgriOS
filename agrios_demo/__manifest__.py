# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "AgriOS Demo",
    "summary": """Load AgriOS demo""",
    "author": "Advance Insight",
    "website": "https://agrios.org",
    "category": "AgriOS",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        # Agrios Modules
        "agrios",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/agrios_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
