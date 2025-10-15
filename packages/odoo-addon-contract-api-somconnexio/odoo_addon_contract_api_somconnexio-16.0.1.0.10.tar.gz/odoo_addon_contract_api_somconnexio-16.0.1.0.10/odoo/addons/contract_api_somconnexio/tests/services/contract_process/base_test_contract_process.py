from faker import Faker

from odoo.addons.somconnexio.tests.sc_test_case import SCTestCase


class BaseContractProcessTestCase(SCTestCase):
    def setUp(self):
        super().setUp()
        self.partner = self.browse_ref("somconnexio.res_partner_2_demo")

        self.iban = self.partner.bank_ids[0].acc_number
        self.mandate = self.browse_ref("somconnexio.demo_mandate_partner_2_demo")
        product = self.browse_ref("somconnexio.TrucadesIllimitades17GB")
        self.crm_lead_line_id = (
            self.env["crm.lead.line"]
            .create(
                {
                    "name": product.name,
                    "iban": self.iban,
                    "product_id": product.id,
                }
            )
            .id
        )
        self.fake = Faker("es-ES")

        self.service_address = {
            "street": self.fake.street_address() + " " + self.fake.secondary_address(),
            "zip_code": self.fake.postcode(),
            "city": self.fake.city(),
            "state": self.browse_ref("base.state_es_m").code,
            "country": self.browse_ref("base.es").code,
        }
