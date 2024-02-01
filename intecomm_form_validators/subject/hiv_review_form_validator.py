from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from edc_constants.constants import PENDING, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_visit_schedule.constants import MONTH0

if TYPE_CHECKING:
    from intecomm_subject.models import HivReview


class HivReviewFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        self.validate_rx_init_dates()
        self.validate_viral_load()

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

    def validate_viral_load(self):
        self.required_if(YES, PENDING, field="has_vl", field_required="drawn_date")
        if self.cleaned_data.get("drawn_date") and self.baseline_datetime:
            if self.cleaned_data.get("drawn_date") <= self.baseline_datetime.date():
                self.raise_validation_error(
                    {
                        "drawn_date": _(
                            "Invalid. Cannot be on or before baseline. "
                            "Report baseline VL result at the baseline visit."
                        )
                    },
                    INVALID_ERROR,
                )
            elif self.hiv_review_for_drawn_date:
                appointment = self.hiv_review_for_drawn_date.related_visit.appointment
                has_vl = self.hiv_review_for_drawn_date.has_vl
                pending_comment = ""
                if has_vl == PENDING:
                    pending_comment = _(
                        "Please update the PENDING viral result on the existing HIV Review . "
                    )
                url = reverse(
                    "intecomm_dashboard:subject_dashboard_url",
                    kwargs=dict(
                        subject_identifier=appointment.subject_identifier,
                        appointment=appointment.id,
                    ),
                )
                visit = (
                    f'<A href="{url}">{appointment.visit_code}."'
                    f'"{appointment.visit_code_sequence}</A>'
                )
                self.raise_validation_error(
                    {
                        "drawn_date": format_html(
                            _(
                                "Invalid. A viral load report with this drawn date already "
                                "exists. %(pending_comment)sSee HIV Review at %(visit)s"
                            )
                            % dict(
                                pending_comment=pending_comment,
                                visit=visit,
                            )
                        )
                    },
                    INVALID_ERROR,
                )
        self.required_if(YES, field="has_vl", field_required="vl")
        self.required_if(YES, field="has_vl", field_required="vl_quantifier")

    @property
    def baseline_datetime(self) -> datetime:
        return self.related_visit_model_cls.objects.get(
            subject_identifier=self.subject_identifier,
            visit_code=MONTH0,
            visit_code_sequence=0,
        ).report_datetime

    @property
    def hiv_review_for_drawn_date(self) -> HivReview | None:
        """Return an HIVReview instance for this drawn date."""
        hiv_review = None
        if self.cleaned_data.get("drawn_date"):
            try:
                hiv_review = self.model.objects.get(
                    subject_visit__subject_identifier=self.subject_identifier,
                    drawn_date=self.cleaned_data.get("drawn_date"),
                )
            except ObjectDoesNotExist:
                hiv_review = None
            else:
                if self.instance.id and hiv_review.id == self.instance.id:
                    hiv_review = None
        return hiv_review
