from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class ComplicationsBaselineFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.required_if(YES, field="stroke", field_required="stroke_ago")
        # self.estimated_date_from_ago("stroke_ago")
        self.required_if(YES, field="heart_attack", field_required="heart_attack_ago")
        # self.estimated_date_from_ago("heart_attack_ago")
        self.required_if(YES, field="renal_disease", field_required="renal_disease_ago")
        # self.estimated_date_from_ago("renal_disease_ago")
        self.required_if(YES, field="vision", field_required="vision_ago")
        # self.estimated_date_from_ago("vision_ago")
        self.required_if(YES, field="numbness", field_required="numbness_ago")
        # self.estimated_date_from_ago("numbness_ago")
        self.required_if(YES, field="foot_ulcers", field_required="foot_ulcers_ago")
        # self.estimated_date_from_ago("foot_ulcers_ago")
        self.required_if(YES, field="complications", field_required="complications_other")
