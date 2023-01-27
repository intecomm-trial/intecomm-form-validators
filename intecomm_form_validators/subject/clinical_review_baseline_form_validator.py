from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator


class ClinicalReviewBaselineFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        pass
        # self.clean_historical_diagnoses()
        # PatientLog.objects.get()

    # def patient_log(self):
    #     return PatientLog.objects.get()
