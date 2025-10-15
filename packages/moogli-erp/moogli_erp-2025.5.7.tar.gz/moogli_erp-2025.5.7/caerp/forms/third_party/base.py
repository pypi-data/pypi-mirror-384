"""
Third party handling forms schemas and related widgets
"""
from collections import OrderedDict

import colander
import deform
import pyvat
from caerp_base.consts import CIVILITE_OPTIONS
from pyramid_deform import CSRFSchema

from caerp import forms
from caerp.models.company import Company
from caerp.models.third_party import ThirdParty


def _build_third_party_select_value(third_party):
    """
    return the tuple for building third_party select
    """
    label = third_party.label
    if third_party.code:
        label += " ({0})".format(third_party.code)
    return (third_party.id, label)


def build_third_party_values(third_parties):
    """
        Build human understandable third_party labels
        allowing efficient discrimination

    :param obj third_parties: Iterable (list or Sqlalchemy query)
    :returns: A list of 2-uples
    """
    return [
        _build_third_party_select_value(third_party) for third_party in third_parties
    ]


def build_admin_third_party_options(query):
    """
    Format options for admin third_party select widget

    :param obj query: The Sqlalchemy query
    :returns: A list of deform.widget.OptGroup
    """
    query = query.order_by(Company.name)
    values = []
    datas = OrderedDict()

    for item in query:
        datas.setdefault(item.company.name, []).append(
            _build_third_party_select_value(item)
        )

    # All third_parties, grouped by Company
    for company_name, third_parties in list(datas.items()):
        values.append(deform.widget.OptGroup(company_name, *third_parties))
    return values


@colander.deferred
def deferred_default_type(node, kw):
    """
    Set the default third_party type based on the current (if in edition mode)
    """
    if isinstance(kw["request"].context, ThirdParty):
        return kw["request"].context.type
    else:
        return colander.null


def tva_intracomm_validator(node, values):
    """
    validator for VAT number. Raise a colander.Invalid exception when
    the value is not a valid vat number.
    """
    if not pyvat.is_vat_number_format_valid(values):
        raise colander.Invalid(node, "TVA intracommunautaire invalide")


def customize_third_party_schema(schema):
    """
    Add common widgets configuration for the third parties forms schema

    :param obj schema: The ThirdParty form schema
    """
    if "civilite" in schema:
        schema["civilite"].widget = forms.get_select(
            CIVILITE_OPTIONS,
        )
        schema["civilite"].validator = colander.OneOf([a[0] for a in CIVILITE_OPTIONS])
    if "additional_address" in schema:
        schema["additional_address"].widget = deform.widget.TextAreaWidget(
            cols=25,
            row=1,
        )
    if "city_code" in schema:
        schema["city_code"].widget = deform.widget.HiddenWidget()
    if "country_code" in schema:
        schema["country_code"].widget = deform.widget.HiddenWidget()

    if "email" in schema:
        schema["email"].validator = forms.mail_validator()
    if "compte_cg" in schema:
        schema[
            "compte_cg"
        ].description = "Laisser vide pour utiliser les paramètres de l'enseigne"
        schema[
            "compte_tiers"
        ].description = "Laisser vide pour utiliser les paramètres de l'enseigne"

    if "tva_intracomm" in schema:
        schema["tva_intracomm"].validator = tva_intracomm_validator

    schema.children.append(CSRFSchema()["csrf_token"])

    if "type" in schema:
        schema["type"].validator = colander.OneOf(["individual", "company", "internal"])
        schema["type"].default = deferred_default_type

    if "bank_account_bic" in schema:
        schema["bank_account_bic"].validator = colander.All(
            forms.bic_validator,
            colander.Length(max=11),
        )
        schema["bank_account_bic"].preparer = forms.remove_spaces_string_preparer
    if "bank_account_iban" in schema:
        schema["bank_account_iban"].validator = colander.All(
            forms.iban_validator,
            colander.Length(max=34),
        )
        schema["bank_account_iban"].preparer = forms.remove_spaces_string_preparer

    return schema
