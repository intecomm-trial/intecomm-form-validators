from __future__ import annotations

from decimal import Decimal
from typing import Tuple

from django.db.models import QuerySet
from django.utils.html import format_html
from edc_constants.constants import DM, HIV, HTN, YES
from edc_utils import round_up


class PatientNotStableError(Exception):
    pass


class PatientNotScreenedError(Exception):
    pass


class PatientNotConsentedError(Exception):
    pass


class PatientGroupRatioError(Exception):
    pass


class PatientGroupSizeError(Exception):
    pass


def verify_patient_group_ratio_raise(
    patients, raise_on_outofrange: bool | None = None
) -> Tuple[int, int, Decimal, bool]:
    ncd = 0.0
    hiv = 0.0
    outofrange = False
    raise_on_outofrange = True if raise_on_outofrange is None else raise_on_outofrange
    for patient_log in patients:
        if patient_log.conditions.filter(name__in=[DM, HTN]).exists():
            ncd += 1.0
        if patient_log.conditions.filter(name__in=[HIV]).exists():
            hiv += 1.0
    if not ncd or not hiv:
        ratio = 0.0
    else:
        ratio = ncd / hiv
    if not (2.0 <= ratio <= 2.7):
        outofrange = True
        if raise_on_outofrange:
            raise PatientGroupRatioError(
                f"Ratio NDC:HIV not met. Expected at least 2:1. Got {int(ncd)}:{int(hiv)}. "
            )
    ncd = int(ncd)
    hiv = int(hiv)
    return int(ncd), int(hiv), Decimal(str(round_up(ratio, 1))), outofrange


def confirm_patient_group_size_or_raise(
    patients: QuerySet | None = None,
    enforce_group_size_min: bool | None = None,
    group_count_min: int | None = None,
) -> None:
    """Confirm at least 14 if complete or override."""
    group_count_min = group_count_min or 14
    enforce_group_size_min = True if enforce_group_size_min is None else enforce_group_size_min
    if not patients:
        raise PatientGroupSizeError("Patient group has no patients.")
    elif enforce_group_size_min and patients.count() < group_count_min:
        raise PatientGroupSizeError(
            f"Patient group must have at least { group_count_min} patients. "
            f"Got {patients.count()}."
        )


def confirm_patient_group_ratio_or_raise(
    patients: QuerySet | None = None,
    enforce_ratio: bool | None = None,
):
    enforce_ratio = True if enforce_ratio is None else enforce_ratio
    if enforce_ratio:
        verify_patient_group_ratio_raise(patients)


def confirm_patients_stable_and_screened_and_consented_or_raise(
    patients: QuerySet | None = None,
):
    if not patients:
        raise PatientGroupSizeError("Patient group has no patients.")
    else:
        for patient_log in patients.all():
            if patient_log.stable != YES:
                errmsg = format_html(
                    "Patient is not known to be stable and in-care. "
                    f'See <a href="{patient_log.get_absolute_url()}">{patient_log}</a>'
                )
                raise PatientNotStableError(errmsg)
            if not patient_log.screening_identifier:
                errmsg = format_html(
                    "Patient has not screened for eligibility. "
                    f'See <a href="{patient_log.get_changelist_url()}">'
                    f"{patient_log}</a>"
                )
                raise PatientNotScreenedError(errmsg)
            if not patient_log.subject_identifier:
                errmsg = format_html(
                    "Patient has not consented. "
                    f'See <a href="{patient_log.get_changelist_url()}">'
                    f"{patient_log}</a>"
                )
                raise PatientNotConsentedError(errmsg)
