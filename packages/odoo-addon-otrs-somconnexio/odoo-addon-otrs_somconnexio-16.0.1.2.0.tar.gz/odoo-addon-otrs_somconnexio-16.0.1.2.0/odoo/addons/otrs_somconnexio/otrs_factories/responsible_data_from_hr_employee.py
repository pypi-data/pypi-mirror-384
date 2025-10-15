from otrs_somconnexio.otrs_models.responsible_data import ResponsibleData


class ResponsibleDataFromHrEmployee:
    def __init__(self, env, user):
        self.user = user
        self.env = env

    def _get_employee_email(self):
        """
        Check if the user has a related employee, to ensure consistency with OTRS agents
        Otherwise return false and OTRS will assign Admin agent
        """
        employee = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.user.id)], limit=1)
        )
        if employee:
            return self.user.email
        return False

    def build(self):
        responsible_params = {
            "email": self._get_employee_email(),
        }
        return ResponsibleData(**responsible_params)
