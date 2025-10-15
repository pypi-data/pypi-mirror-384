from mock import patch
from odoo.tools import html2plaintext
from ..sc_test_case import SCTestCase
from odoo.exceptions import ValidationError, MissingError


@patch(
    "odoo.addons.somconnexio.services.fiber_contract_to_pack.FiberContractToPackService.create"  # noqa
)
class TestCreateLeadfromPartnerWizard(SCTestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.mbl_categ = self.env.ref("somconnexio.mobile_service")
        self.fiber_categ = self.env.ref("somconnexio.broadband_fiber_service")
        self.partner = self.browse_ref("somconnexio.res_partner_2_demo")
        self.company_partner = self.browse_ref("somconnexio.res_partner_company_demo")
        # set current user as employee to ensure user_id assingment on create CRM
        self.env["hr.employee"].create(
            {"name": self.env.user.name, "user_id": self.env.user.id}
        )
        self.bank = self.partner.bank_ids[0]
        self.email = self.env["res.partner"].create(
            {
                "parent_id": self.partner.id,
                "email": "new_email@test.com",
                "type": "contract-email",
            }
        )
        self.partner.phone = "888888888"

        self.wizard_params = {
            "source": "others",
            "bank_id": self.partner.bank_ids.id,
            "email_id": self.email.id,
            "product_id": self.ref("somconnexio.SenseMinuts2GB"),
            "product_categ_id": self.mbl_categ.id,
            "type": "new",
            "delivery_street": "Principal A",
            "delivery_zip_code": "08027",
            "delivery_city": "Barcelona",
            "delivery_state_id": self.ref("base.state_es_b"),
            "invoice_street": "Principal B",
            "invoice_zip_code": "08015",
            "invoice_city": "Barcelona",
            "invoice_state_id": self.ref("base.state_es_b"),
            "notes": "This is a test note",
        }
        self.service_address = {
            "service_street": "Principal A",
            "service_zip_code": "00123",
            "service_city": "Barcelona",
            "service_state_id": self.ref("base.state_es_b"),
        }

    def test_create_new_mobile_lead(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        self.assertFalse(wizard.is_service_address_required)
        self.assertTrue(wizard.is_delivery_address_required)
        self.assertFalse(wizard.fiber_contract_to_link)
        self.assertEqual(wizard.has_mobile_pack_offer_text, "no")

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertEqual(
            crm_lead_action.get("xml_id"), "somconnexio.crm_case_form_view_pack"
        )

        self._assert_crm_lead(crm_lead)
        self.assertEqual(
            html2plaintext(crm_lead_line.notes), self.wizard_params["notes"]
        )
        self.assertEqual(crm_lead_line.mobile_isp_info.type, "new")
        self.assertEqual(
            crm_lead_line.product_id, self.browse_ref("somconnexio.SenseMinuts2GB")
        )
        self.assertEqual(crm_lead_line.iban, self.partner.bank_ids.sanitized_acc_number)
        self.assertEqual(crm_lead_line.mobile_isp_info.delivery_street, "Principal A")
        self.assertEqual(crm_lead_line.mobile_isp_info.delivery_zip_code, "08027")
        self.assertEqual(crm_lead_line.mobile_isp_info.delivery_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.mobile_isp_info.delivery_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.mobile_isp_info.delivery_country_id,
            self.browse_ref("base.es"),
        )
        self.assertEqual(crm_lead_line.mobile_isp_info.invoice_street, "Principal B")
        self.assertEqual(crm_lead_line.mobile_isp_info.invoice_zip_code, "08015")
        self.assertEqual(crm_lead_line.mobile_isp_info.invoice_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.mobile_isp_info.invoice_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.mobile_isp_info.invoice_country_id, self.browse_ref("base.es")
        )
        self.assertFalse(
            crm_lead_line.mobile_isp_info.linked_fiber_contract_id,
        )

    def test_create_portability_mobile_lead(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")

        self.wizard_params.update(
            {
                "source": "others",
                "icc": "666",
                "type": "portability",
                "previous_contract_type": "contract",
                "phone_number": "666666666",
                "donor_icc": "3333",
                "previous_mobile_provider": self.ref("somconnexio.previousprovider4"),
                "previous_owner_vat_number": "52736216E",
                "previous_owner_first_name": "Firstname test",
                "previous_owner_name": "Lastname test",
            }
        )
        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )
        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertEqual(
            wizard.available_products,
            self.env["product.product"].search(
                self._get_expected_product_domain(wizard.product_categ_id)
            ),
        )

        self.assertEqual(
            crm_lead_action.get("xml_id"), "somconnexio.crm_case_form_view_pack"
        )

        self._assert_crm_lead(crm_lead)
        self.assertEqual(
            crm_lead_line.product_id, self.browse_ref("somconnexio.SenseMinuts2GB")
        )
        self.assertEqual(crm_lead_line.iban, self.partner.bank_ids.sanitized_acc_number)
        self.assertEqual(crm_lead_line.mobile_isp_info.icc, "666")
        self.assertEqual(crm_lead_line.mobile_isp_info.type, "portability")
        self.assertEqual(
            crm_lead_line.mobile_isp_info.previous_contract_type, "contract"
        )
        self.assertEqual(crm_lead_line.mobile_isp_info.phone_number, "666666666")
        self.assertEqual(crm_lead_line.mobile_isp_info.icc_donor, "3333")
        self.assertEqual(
            crm_lead_line.mobile_isp_info.previous_provider,
            self.browse_ref("somconnexio.previousprovider4"),
        )
        self.assertEqual(
            crm_lead_line.mobile_isp_info.previous_owner_vat_number, "ES52736216E"
        )
        self.assertEqual(
            crm_lead_line.mobile_isp_info.previous_owner_first_name, "Firstname test"
        )
        self.assertEqual(
            crm_lead_line.mobile_isp_info.previous_owner_name, "Lastname test"
        )
        self.assertEqual(crm_lead_line.mobile_isp_info.delivery_street, "Principal A")
        self.assertEqual(crm_lead_line.mobile_isp_info.delivery_zip_code, "08027")
        self.assertEqual(crm_lead_line.mobile_isp_info.delivery_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.mobile_isp_info.delivery_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.mobile_isp_info.delivery_country_id,
            self.browse_ref("base.es"),
        )
        self.assertFalse(
            crm_lead_line.mobile_isp_info.linked_fiber_contract_id,
        )

    def test_create_new_mobile_lead_with_icc(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")

        self.wizard_params["icc"] = "666"

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.company_partner.id)
            .create(self.wizard_params)
        )

        self.assertFalse(wizard.is_service_address_required)
        self.assertFalse(wizard.is_delivery_address_required)

        crm_lead_action = wizard.create_lead()

        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self._assert_crm_lead(crm_lead, self.company_partner)
        self.assertEqual(crm_lead_line.mobile_isp_info.icc, "666")

    def test_default_team_id_is_company(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.return_value = MissingError("")

        user_employee = self.env["res.users"].create(
            {
                "name": "User Employee",
                "login": "user_employee",
            }
        )
        employee = self.env["hr.employee"].create(
            {
                "name": "Test employee",
                "user_id": user_employee.id,
            }
        )

        self.assertTrue(self.company_partner.is_company)

        self.wizard_params.update(
            {
                "bank_id": self.company_partner.bank_ids[0].id,
                "email_id": self.company_partner.id,
                "confirmed_documentation": True,
                "employee_id": employee.id,
            }
        )

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.company_partner.id)
            .create(self.wizard_params)
        )
        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])

        self._assert_crm_lead(
            crm_lead,
            self.company_partner,
            self.company_partner.email,
            True,
            user_employee,
        )

    def test_create_new_BA_lead(self, mock_get_fiber_contracts):

        self.wizard_params.update(
            {
                "source": "others",
                "product_id": self.ref("somconnexio.Fibra600Mb"),
                "product_categ_id": self.fiber_categ.id,
                **self.service_address,
            }
        )

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        self.assertTrue(wizard.is_service_address_required)
        self.assertFalse(wizard.is_delivery_address_required)

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertEqual(
            crm_lead_action.get("xml_id"), "somconnexio.crm_case_form_view_pack"
        )

        self._assert_crm_lead(crm_lead)
        self.assertEqual(
            html2plaintext(crm_lead_line.notes), self.wizard_params["notes"]
        )
        self.assertEqual(
            crm_lead_line.product_id, self.browse_ref("somconnexio.Fibra600Mb")
        )
        self.assertEqual(crm_lead_line.iban, self.partner.bank_ids.sanitized_acc_number)
        self.assertEqual(crm_lead_line.broadband_isp_info.type, "new")
        self.assertEqual(crm_lead_line.broadband_isp_info.service_street, "Principal A")
        self.assertEqual(crm_lead_line.broadband_isp_info.service_zip_code, "00123")
        self.assertEqual(crm_lead_line.broadband_isp_info.service_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.broadband_isp_info.service_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_country_id,
            self.browse_ref("base.es"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_street, "Principal A"
        )
        self.assertEqual(crm_lead_line.broadband_isp_info.delivery_zip_code, "08027")
        self.assertEqual(crm_lead_line.broadband_isp_info.delivery_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_country_id,
            self.browse_ref("base.es"),
        )
        mock_get_fiber_contracts.assert_not_called()

    def test_create_portability_BA_lead(self, _):
        self.wizard_params.update(
            {
                "source": "others",
                "product_id": self.ref("somconnexio.Fibra600Mb"),
                "product_categ_id": self.fiber_categ.id,
                "type": "portability",
                "previous_owner_vat_number": "52736216E",
                "previous_owner_first_name": "Test",
                "previous_owner_name": "Test",
                "keep_landline": True,
                "landline": "972972972",
                "previous_BA_service": "fiber",
                "previous_BA_provider": self.ref("somconnexio.previousprovider3"),
                **self.service_address,
            }
        )

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertEqual(
            crm_lead_action.get("xml_id"), "somconnexio.crm_case_form_view_pack"
        )

        self._assert_crm_lead(crm_lead)
        self.assertEqual(
            crm_lead_line.product_id, self.browse_ref("somconnexio.Fibra600Mb")
        )
        self.assertEqual(crm_lead_line.broadband_isp_info.type, "portability")
        self.assertTrue(crm_lead_line.broadband_isp_info.keep_phone_number)
        self.assertEqual(
            crm_lead_line.broadband_isp_info.previous_provider,
            self.browse_ref("somconnexio.previousprovider3"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.previous_service,
            "fiber",
        )
        self.assertEqual(crm_lead_line.broadband_isp_info.service_street, "Principal A")
        self.assertEqual(crm_lead_line.broadband_isp_info.service_zip_code, "00123")
        self.assertEqual(crm_lead_line.broadband_isp_info.service_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.broadband_isp_info.service_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.service_country_id,
            self.browse_ref("base.es"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_street, "Principal A"
        )
        self.assertEqual(crm_lead_line.broadband_isp_info.delivery_zip_code, "08027")
        self.assertEqual(crm_lead_line.broadband_isp_info.delivery_city, "Barcelona")
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_state_id,
            self.browse_ref("base.state_es_b"),
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.delivery_country_id,
            self.browse_ref("base.es"),
        )

    def test_create_portability_mobile_without_phone_number(self, _):
        self.wizard_params.update(
            {
                "source": "others",
                "icc": "666",
                "type": "portability",
                "previous_contract_type": "contract",
                "donor_icc": "3333",
                "previous_mobile_provider": self.ref("somconnexio.previousprovider4"),
                "previous_owner_vat_number": "52736216E",
                "previous_owner_first_name": "Firstname test",
                "previous_owner_name": "Lastname test",
            }
        )

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        self.assertRaises(ValidationError, wizard.create_lead)

    def test_create_portability_ba_keep_landline_without_number(self, _):
        self.wizard_params.update(
            {
                "source": "others",
                "product_id": self.ref("somconnexio.Fibra600Mb"),
                "product_categ_id": self.fiber_categ.id,
                "type": "portability",
                "previous_owner_vat_number": "52736216E",
                "previous_owner_first_name": "Test",
                "previous_owner_name": "Test",
                "keep_landline": True,
                "previous_BA_service": "fiber",
                "previous_BA_provider": self.ref("somconnexio.previousprovider4"),
                **self.service_address,
            }
        )

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        self.assertRaises(ValidationError, wizard.create_lead)

    def test_set_phone_to_partner_if_none(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")

        self.partner.phone = False
        self.partner.mobile = False
        self.wizard_params["phone_contact"] = "666666666"

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        self.assertFalse(self.partner.phone)

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])

        self.assertEqual(self.partner.phone, wizard.phone_contact)
        self.assertEqual(crm_lead.phone, wizard.phone_contact)

    def test_default_phone_contact_partner_mobile_over_phone(
        self, mock_get_fiber_contracts
    ):
        mock_get_fiber_contracts.side_effect = MissingError("")
        self.partner.mobile = "666777888"

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )
        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])

        self.assertEqual(wizard.phone_contact, self.partner.mobile)
        self.assertEqual(wizard.phone_contact, crm_lead.phone)

    def test_fiber_contract_to_link(self, mock_get_fiber_contracts):
        fiber_contract = self.env.ref("somconnexio.contract_fibra_600")
        mock_get_fiber_contracts.return_value = [fiber_contract]

        self.wizard_params.update(
            {
                "product_id": self.ref("somconnexio.TrucadesIllimitades20GBPack"),
            }
        )
        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )
        self.assertTrue(wizard.fiber_contract_to_link)
        self.assertEqual(wizard.has_mobile_pack_offer_text, "yes")

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertEqual(
            crm_lead_line.mobile_isp_info.linked_fiber_contract_id, fiber_contract
        )
        self.assertEqual(
            wizard.available_products,
            self.env["product.product"].search(
                self._get_expected_product_domain(
                    wizard.product_categ_id, pack_product=True
                )
            ),
        )

    def test_crm_lead_name_source(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")

        source = "outgoing_call"
        self.wizard_params["source"] = source

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])

        self.assertEqual(crm_lead.source, source)
        self.assertEqual(crm_lead.name, wizard.title)

    def _get_expected_product_domain(
        self, product_categ, pack_product=False, business=False
    ):
        product_templs = self.env["product.template"].search(
            [
                ("categ_id", "=", product_categ.id),
                ("name", "not ilike", "borda"),
            ]
        )
        expected_domain = [
            ("product_tmpl_id", "in", product_templs.ids),
            ("pack_ok", "=", False),
        ]

        attr_to_exclude = self.env["product.attribute.value"]

        if not pack_product:
            attr_to_exclude |= self.env.ref("somconnexio.IsInPack")
        if business:
            attr_to_exclude |= self.env.ref("somconnexio.ParticularExclusive")
        else:
            attr_to_exclude |= self.env.ref("somconnexio.CompanyExclusive")

        if attr_to_exclude:
            product_template_attribute_value_ids = self.env[
                "product.template.attribute.value"
            ].search(
                [
                    ("product_attribute_value_id", "in", attr_to_exclude.ids),
                    ("product_tmpl_id", "in", product_templs.ids),
                ]
            )

            expected_domain.extend(
                [
                    (
                        "product_template_attribute_value_ids",
                        "not in",
                        product_template_attribute_value_ids.ids,
                    ),
                ]
            )

        return expected_domain

    def _assert_crm_lead(
        self,
        crm_lead,
        partner=None,
        email=None,
        confirmed_documentation=False,
        user=None,
        team_id=None,
    ):
        if partner is None:
            partner = self.partner
        if email is None:
            email = self.email.email
        if team_id is None:
            team_id = (
                self.env.ref("somconnexio.business")
                if partner.is_company
                else self.env.ref("somconnexio.residential")
            )
        if user is None:
            user = self.env.user

        self.assertEqual(crm_lead.partner_id, partner)
        self.assertEqual(crm_lead.email_from, email)
        self.assertEqual(crm_lead.user_id, user)
        self.assertEqual(crm_lead.confirmed_documentation, confirmed_documentation)
        self.assertEqual(
            crm_lead.team_id,
            team_id,
        )
