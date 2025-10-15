import logging

from .ba import BAContractProcess

_logger = logging.getLogger(__name__)


class Router4GContractProcess(BAContractProcess):
    _name = "router.4g.contract.process"
    _inherit = "ba.contract.process"
    _description = """
        ADSL Contract creation
    """

    @staticmethod
    def validate_service_technology_deps(params):
        pass

    def _create_router_4G_contract_service_info(self, params):
        if not params:
            return False

        router_product = self._get_router_product_id(params["router_product_id"])
        return (
            self.env["router.4g.service.contract.info"]
            .sudo()
            .create(
                {
                    "phone_number": params["phone_number"],
                    "imei": params.get("IMEI"),
                    "ssid": params.get("SSID"),
                    "pin": params.get("PIN"),
                    "router_acces": params.get("router_acces"),
                    "password_wifi": params.get("password_wifi"),
                    "router_product_id": router_product.id,
                    "icc": params["icc"],
                    "icc_subs": params.get("icc_subs"),
                }
            )
        )
