from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from edc_constants.constants import HIV, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import (
    get_initial_review_model_cls,
    get_review_model_cls,
    raise_if_clinical_review_does_not_exist,
)
from edc_form_validators import FormValidator


class HivReviewFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.applicable_if_true(
            not self.is_rx_initiated(),
            field_applicable="rx_init",
            applicable_msg="Subject was NOT previously reported as on ART.",
            not_applicable_msg="Subject was previously reported as on ART.",
        )
        self.required_if(
            YES, field="arv_initiated", field_required="arv_initiation_actual_date"
        )

    def is_rx_initiated(self) -> bool:
        """Return True if already initiated"""
        try:
            get_initial_review_model_cls(HIV).objects.get(
                subject_visit__subject_identifier=self.subject_identifier,
                report_datetime__lte=self.report_datetime,
                rx_init=YES,
            )
        except ObjectDoesNotExist:
            rx_initiated = (
                get_review_model_cls(HIV)
                .objects.filter(
                    subject_visit__subject_identifier=self.subject_identifier,
                    report_datetime__lte=self.report_datetime,
                    rx_init=YES,
                )
                .exists()
            )
        else:
            rx_initiated = True
        return rx_initiated
