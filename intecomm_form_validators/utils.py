from __future__ import annotations

from decimal import Decimal
from typing import Tuple

from django.conf import settings
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


class PatientGroupMakeupError(Exception):
    pass


def get_min_group_size() -> int:
    return getattr(settings, "INTECOMM_MIN_GROUP_SIZE", 14)


def get_min_group_size_for_ratio() -> int:
    return getattr(settings, "INTECOMM_MIN_GROUP_SIZE_FOR_RATIO", 9)


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
    bypass_group_size_min: bool | None = None,
    group_count_min: int | None = None,
) -> None:
    """Confirm at least 14 if complete or override."""
    group_count_min = group_count_min or get_min_group_size()
    if not patients:
        raise PatientGroupSizeError("Patient group has no patients.")
    elif not bypass_group_size_min and patients.count() < group_count_min:
        raise PatientGroupSizeError(
            f"Patient group must have at least {group_count_min} patients. "
            f"Got {patients.count()}."
        )


def confirm_patient_group_minimum_of_each_condition_or_raise(
    patients: QuerySet | None = None,
) -> None:
    """Confirm at least 2 of each condition

    A minimum of two people with each of HIV, diabetes and
    hypertension will be selected per group. The rest will be
    patients with a variable mixture of the three conditions
    """
    hiv_only = 0
    for patient in patients.all():
        hiv_only += patient.conditions.filter(name=HIV).exclude(name__in=[DM, HTN]).count()
        if hiv_only >= 2:
            break
    if hiv_only < 2:
        raise PatientGroupMakeupError(
            f"Patient group must have at least 2 HIV only patients. Got {hiv_only}."
        )

    ncd_only = 0
    for patient in patients.all():
        ncd_only += patient.conditions.filter(name__in=[DM, HTN]).exclude(name=HIV).count()
        if ncd_only >= 4:
            break
    if ncd_only < 4:
        raise PatientGroupMakeupError(
            f"Patient group must have at least 4 NCD only patients. Got {ncd_only}."
        )


def confirm_patient_group_ratio_or_raise(
    patients: QuerySet | None = None,
    bypass_group_ratio: bool | None = None,
):
    if not bypass_group_ratio:
        verify_patient_group_ratio_raise(patients)


def confirm_patients_stable_and_screened_and_consented_or_raise(
    patients: QuerySet | None = None,
):
    if not patients:
        raise PatientGroupSizeError("Patient group has no patients.")
    else:
        for patient_log in patients.all():
            link = (
                f'See <a href="{patient_log.get_changelist_url()}?'
                f'q={str(patient_log.id)}">{patient_log}</a>'
            )
            if patient_log.stable != YES:
                errmsg = format_html(f"Patient is not known to be stable and in-care. {link}.")
                raise PatientNotStableError(errmsg)
            if not patient_log.screening_identifier:
                errmsg = format_html(f"Patient has not screened for eligibility. {link}.")
                raise PatientNotScreenedError(errmsg)
            if not patient_log.subject_identifier:
                errmsg = format_html(f"Patient has not consented. {link}.")
                raise PatientNotConsentedError(errmsg)
