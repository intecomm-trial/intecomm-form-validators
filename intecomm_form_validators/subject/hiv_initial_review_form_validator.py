from django import forms
from edc_constants.constants import NO, OTHER, PENDING, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.medical_date import DxDate, MedicalDateError
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator
from edc_model.utils import estimated_date_from_ago


class HivInitialReviewFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def __init__(self, **kwargs):
        self.dx_date = None
        super().__init__(**kwargs)

    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))

        try:
            self.dx_date = DxDate(self.cleaned_data)
        except MedicalDateError as e:
            self.raise_validation_error(e.message_dict, e.code)

        self.applicable_if(YES, field="receives_care", field_applicable="clinic")

        self.required_if(OTHER, field="clinic", field_required="clinic_other")

        self.required_if(YES, field="receives_care", field_required="rx_init")

        self.validate_art_initiation_date()

        self.required_if(YES, field="rx_init", field_required="has_vl")
        self.validate_viral_load()

        self.required_if(YES, field="rx_init", field_required="has_cd4")
        self.validate_cd4()

    def validate_art_initiation_date(self):
        self.not_required_if(
            NO,
            field="rx_init",
            field_required="rx_init_date",
            inverse=False,
        )
        self.not_required_if(
            NO,
            field="rx_init",
            field_required="rx_init_ago",
            inverse=False,
        )

        if self.cleaned_data.get("rx_init") == YES and not (
            self.cleaned_data.get("rx_init_ago") or self.cleaned_data.get("rx_init_date")
        ):
            raise forms.ValidationError(
                {"rx_init_date": "This field is required (or the below)."}
            )

        if (
            self.cleaned_data.get("rx_init") == YES
            and self.cleaned_data.get("rx_init_ago")
            and self.cleaned_data.get("rx_init_date")
        ):
            raise forms.ValidationError(
                {
                    "rx_init_ago": (
                        "This field is not required if the actual date is provided (below)."
                    )
                }
            )

        if self.arv_initiation_date and self.dx_date:
            if self.arv_initiation_date < self.dx_date:
                field = self.which_field(
                    ago_field="rx_init_ago",
                    date_field="rx_init_date",
                )
                raise forms.ValidationError(
                    {field: "Invalid. Cannot start ART before HIV diagnosis."}
                )

    def validate_viral_load(self):
        self.required_if(YES, PENDING, field="has_vl", field_required="drawn_date")
        if self.cleaned_data.get("drawn_date") and self.dx_date:
            if self.cleaned_data.get("drawn_date") < self.dx_date:
                raise forms.ValidationError(
                    {"drawn_date": "Invalid. Cannot be before HIV diagnosis."}
                )
        self.required_if(YES, field="has_vl", field_required="vl")
        self.required_if(YES, field="has_vl", field_required="vl_quantifier")

    def validate_cd4(self):
        self.required_if(YES, field="has_cd4", field_required="cd4")
        self.required_if(YES, field="has_cd4", field_required="cd4_date")
        if self.cleaned_data.get("cd4_date") and self.dx_date:
            if self.cleaned_data.get("cd4_date") < self.dx_date:
                raise forms.ValidationError(
                    {"cd4_date": "Invalid. Cannot be before HIV diagnosis."}
                )

    @property
    def arv_initiation_date(self):
        if self.cleaned_data.get("rx_init_ago"):
            return estimated_date_from_ago(
                cleaned_data=self.cleaned_data, ago_field="rx_init_ago"
            )
        return self.cleaned_data.get("rx_init_date")

    def which_field(self, ago_field=None, date_field=None):
        if self.cleaned_data.get(ago_field):
            return ago_field
        if self.cleaned_data.get(date_field):
            return date_field
        return None
