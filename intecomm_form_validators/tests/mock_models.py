from django_mock_queries.query import MockModel


class SubjectScreeningMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "SubjectScreening"
        super().__init__(*args, **kwargs)
        self._meta.label_lower = "intecomm_screening.subjectscreening"

    def __str__(self):
        return str(self.screening_identifier)


class PatientGroupMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "PatientGroup"
        super().__init__(*args, **kwargs)
        self._meta.label_lower = "intecomm_screening.patientgroup"
        self.user_created = "frisco"
        self.user_modified = "frisco"

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self) -> str:
        return "absolute_url"

    def get_changelist_url(self, search_term=None) -> str:
        return "changelist_url"

    def refresh_from_db(self):
        pass


class PatientLogMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "PatientLog"
        super().__init__(*args, **kwargs)
        self._meta.label_lower = "intecomm_screening.patientlog"

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self) -> str:
        return "absolute_url"

    def get_changelist_url(self, search_term=None) -> str:
        return "changelist_url"


class ConditionsMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "Conditions"
        super().__init__(*args, **kwargs)
        self._meta.label_lower = "intecomm_list.condition"
