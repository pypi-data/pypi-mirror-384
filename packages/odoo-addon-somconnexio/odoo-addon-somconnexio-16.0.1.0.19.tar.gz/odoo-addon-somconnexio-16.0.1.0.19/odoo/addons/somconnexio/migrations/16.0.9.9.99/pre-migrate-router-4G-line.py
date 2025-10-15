import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("SELECT id,vodafone_id from router_4g_service_contract_info")
    _logger.info(
        "router_4g_service_contract_info.vodafone_id copied to router_4g_service_contract_info.phone_number"  # noqa E501
    )
    contract_infos = cr.fetchall()
    for contract_info in contract_infos:
        id = contract_info[0]
        vodafone_id = contract_info[1] or False
        cr.execute(
            (
                "UPDATE router_4g_service_contract_info SET phone_number={} WHERE id={}"
            ).format(vodafone_id, id)
        )
