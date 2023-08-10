from __future__ import annotations

from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import INVALID_ERROR, FormValidator


class HivReviewFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        self.validate_rx_init_dates()

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
