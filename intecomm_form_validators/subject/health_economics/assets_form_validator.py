from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_crf.utils import raise_if_crf_does_not_exist
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class HealthEconomicsAssetsFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicshouseholdhead",
        )
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicspatient",
        )
        self.validate_other_specify(field="water_source")
        self.validate_other_specify(field="toilet")
        self.validate_other_specify(field="roof_material")
        self.validate_other_specify(field="external_wall_material")
        self.validate_other_specify(field="external_window_material")
        self.validate_other_specify(field="floor_material")
        self.validate_other_specify(field="light_source")
        self.validate_other_specify(field="cooking_fuel")
