# Copyright 2019 Camptocamp SA
# Copyright 2019 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Storage Type ABC Strategy",
    "summary": "Advanced storage strategy ABC for WMS",
    "version": "18.0.1.0.1",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/stock-logistics-putaway",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock_storage_type"],
    "data": ["views/product.xml", "views/stock_location.xml"],
}
