{
    "name": "Contract API - SomConnexio",
    "version": "16.0.1.0.10",
    "summary": """
        Expose the REST API used in Som Connexió to create and manage contracts in Odoo.
    """,
    "author": "Som Connexió SCCL, Coopdevs Treball SCCL",
    "website": "https://git.coopdevs.org/coopdevs/som-connexio/odoo/odoo-somconnexio",
    "license": "AGPL-3",
    "category": "Cooperative Management",
    "depends": [
        "contract_group_somconnexio",
        "res_partner_api_somconnexio",
        "switchboard_somconnexio",
        "somconnexio",
    ],
    "data": [],
    "demo": [],
    "external_dependencies": {"python": ["faker"]},
    "application": False,
    "installable": True,
}
