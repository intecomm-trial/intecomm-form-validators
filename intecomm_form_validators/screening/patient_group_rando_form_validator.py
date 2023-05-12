from django.urls import reverse
from django.utils.html import format_html
from edc_constants.constants import COMPLETE, YES
from edc_form_validators import INVALID_ERROR, FormValidator

INVALID_RANDOMIZE = "INVALID_RANDOMIZE"
INVALID_COMPLETE_GROUP_FIRST = "INVALID_COMPLETE_GROUP_FIRST"
INVALID_STATUS_NOT_COMPLETE = "INVALID_STATUS_NOT_COMPLETE"


class PatientGroupRandoFormValidator(FormValidator):
    def clean(self):
        self.block_changes_if_already_randomized()
        if not self.cleaned_data.get("name"):
            raise self.raise_validation_error(
                {"name": "This field is required"}, INVALID_ERROR
            )
        if not self.instance.id:
            raise self.raise_validation_error(
                "Complete Patient Group form first", INVALID_COMPLETE_GROUP_FIRST
            )
        if not self.instance.status == COMPLETE:
            url = reverse(
                "intecomm_screening_admin:intecomm_screening_patientgroup_change",
                args=(self.instance.id,),
            )
            raise self.raise_validation_error(
                format_html(
                    f'Return to the <A href="{url}">'
                    "Patient Group form</A> and verify the status is set to COMPLETE"
                ),
                INVALID_STATUS_NOT_COMPLETE,
            )
        if (
            self.cleaned_data.get("randomize_now") == YES
            and self.cleaned_data.get("confirm_randomize_now") != "RANDOMIZE"
        ):
            self.raise_validation_error(
                {
                    "confirm_randomize_now": (
                        "If you wish to randomize this group, please confirm"
                    )
                },
                INVALID_RANDOMIZE,
            )
        self.not_required_if_true(
            self.cleaned_data.get("randomize_now") != YES,
            field="confirm_randomize_now",
            msg="Only complete if you are ready to randomize now.",
        )

    def block_changes_if_already_randomized(self):
        if self.instance.randomized:
            self.raise_validation_error(
                "A randomized group may not be changed", INVALID_RANDOMIZE
            )
