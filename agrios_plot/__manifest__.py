# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "AgriOS Plot",
    "summary": """Efficiently plots of land and agricultural data""",
    "author": "Advance Insight",
    "website": "https://agrios.org",
    "category": "AgriOS",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        # Odoo Modules
        "product",
        # OCA Modules
        # Agrios Modules
        "agrios_farmer",
    ],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "data/uom_uom_data.xml",
        "data/product_category_data.xml",
        "views/farmer_plot_crop_area_views.xml",
        "views/farmer_plot_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/ir_actions_act_window.xml",
        "views/ir_ui_menu.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [
        "demo/farmer_plot_demo.xml",
        "demo/product_product_demo.xml",
        "demo/res_partner_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "agrios_plot/static/src/lib/leaflet/leaflet.css",
            "agrios_plot/static/src/lib/leaflet/leaflet.js",
            "agrios_plot/static/src/lib/leaflet.draw/leaflet.draw.css",
            "agrios_plot/static/src/lib/leaflet.draw/leaflet.draw.js",
            "agrios_plot/static/src/components/map_widget/*",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
