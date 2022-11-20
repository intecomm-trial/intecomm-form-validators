from edc_form_validators import INVALID_ERROR, FormValidator


class PatientGroupFormValidator(FormValidator):

    group_count_min = 14

    def clean(self):

        self.raise_validation_error({"__all__": "This form may not be changed"}, INVALID_ERROR)
