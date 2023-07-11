from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from edc_constants.constants import HIV, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import (
    get_initial_review_model_cls,
    get_review_model_cls,
    raise_if_clinical_review_does_not_exist,
)
from edc_form_validators import INVALID_ERROR, FormValidator


class HivReviewFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.applicable_if_true(
            not self.is_rx_initiated(),
            field_applicable="rx_init",
            applicable_msg="Subject was NOT previously reported as on ART.",
            not_applicable_msg="Subject was previously reported as on ART.",
        )
        self.validate_rx_init_dates()

    def is_rx_initiated(self) -> bool:
        """Return True if already initiated"""
        try:
            get_initial_review_model_cls(HIV).objects.get(
                subject_visit__subject_identifier=self.subject_identifier,
                report_datetime__lte=self.report_datetime,
                rx_init=YES,
            )
        except ObjectDoesNotExist:
            if self.instance.id:
                exclude = {"id": self.instance.id}
            rx_initiated = (
                get_review_model_cls(HIV)
                .objects.filter(
                    subject_visit__subject_identifier=self.subject_identifier,
                    report_datetime__lte=self.report_datetime,
                    rx_init=YES,
                )
                .exclude(**exclude)
                .exists()
            )
        else:
            rx_initiated = True
        return rx_initiated

    def validate_rx_init_dates(self):
        rx_init = self.cleaned_data.get("rx_init")
        rx_init_date = self.cleaned_data.get("rx_init_date")
        rx_init_ago = self.cleaned_data.get("rx_init_ago")
        if rx_init and rx_init == YES:
            if rx_init_date and rx_init_ago:
                self.raise_validation_error(
                    {"rx_init_ago": "This field is not required"}, INVALID_ERROR
                )
            elif not rx_init_date and not rx_init_ago:
                self.raise_validation_error(
                    {"rx_init_date": "This field is required"}, INVALID_ERROR
                )
            elif not rx_init_date and rx_init_ago:
                pass
            elif rx_init_date and not rx_init_ago:
                pass
        elif rx_init and rx_init != YES:
            if rx_init_date:
                self.raise_validation_error(
                    {"rx_init_date": "This field is not required"}, INVALID_ERROR
                )
            if rx_init_ago:
                self.raise_validation_error(
                    {"rx_init_ago": "This field is not required"}, INVALID_ERROR
                )
