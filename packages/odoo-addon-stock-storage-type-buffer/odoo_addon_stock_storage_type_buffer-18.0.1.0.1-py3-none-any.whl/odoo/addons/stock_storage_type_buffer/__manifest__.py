# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Storage Type Buffers",
    "summary": "Exclude storage locations from put-away if their buffer is full",
    "version": "18.0.1.0.1",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/stock-logistics-putaway",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock_storage_type"],
    "data": [
        "views/stock_location_storage_buffer_views.xml",
        "templates/stock_location_storage_buffer_templates.xml",
        "security/ir.model.access.csv",
    ],
}
