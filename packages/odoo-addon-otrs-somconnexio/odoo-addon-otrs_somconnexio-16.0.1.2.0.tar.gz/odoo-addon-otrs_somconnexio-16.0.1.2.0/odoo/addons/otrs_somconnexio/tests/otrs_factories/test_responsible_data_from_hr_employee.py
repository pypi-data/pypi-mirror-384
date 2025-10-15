from odoo.addons.somconnexio.tests.sc_test_case import SCTestCase

from ...otrs_factories.responsible_data_from_hr_employee import (
    ResponsibleDataFromHrEmployee,
)


class ResponsibleDataFromHrEmployeeTest(SCTestCase):
    def test_build_with_not_employee_user(self):
        responsile_data = ResponsibleDataFromHrEmployee(self.env, self.env.user).build()
        self.assertFalse(responsile_data.email)

    def test_build_with_employee_user(self):
        self.env["hr.employee"].create(
            {"name": self.env.user.name, "user_id": self.env.user.id}
        )
        responsile_data = ResponsibleDataFromHrEmployee(self.env, self.env.user).build()
        self.assertEqual(responsile_data.email, self.env.user.email)
