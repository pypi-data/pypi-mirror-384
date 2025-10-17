"""Model builder module.

Provides some helper methods for easier work with basyx sdk data model
"""

import uuid
from typing import Any

from basyx.aas import model


def create_unique_short_id(id_short: str) -> str:
    """Generate a unique identifier string by appending a UUID to the provided ID short.

    :param id_short: provided ID short
    :return: unique identifier
    """
    return f"{id_short}_{str(uuid.uuid4()).replace('-', '_')}"


def create_base_submodel_element_property(
    id_short: str, type: model.datatypes, value: Any, display_name: str = "", description: str = ""
) -> model.Property:
    """Create a basic SubmodelElement of type Property."""
    sme = model.Property(id_short=id_short, value_type=type, value=value)

    if not description:
        description = f"This is the submodel element with ID short '{id_short}'"

    description_text = {"en": f"{description}"}
    sme.description = model.MultiLanguageTextType(description_text)

    if not display_name:
        display_name = "POC Submodel Element"

    display_name_text = {"en": f"{display_name}"}
    sme.display_name = model.MultiLanguageTextType(display_name_text)

    return sme


def create_base_submodel(identifier: str, id_short: str, display_name: str = "", description: str = "") -> model.Submodel:
    """Create a basic Submodel.

    :param identifier: identifier of the Submodel
    :param id_short: ID short of the Submodel
    :param display_name: display name of the Submodel, defaults to ""
    :param description: description of the Submodel, defaults to ""
    :return: Submodel instance
    """
    sm = model.Submodel(identifier)
    sm.id_short = id_short

    if not description:
        description = f"This is the submodel with ID short '{id_short}'"

    description_text = {"en": f"{description}"}
    sm.description = model.MultiLanguageTextType(description_text)

    if not display_name:
        display_name = "POC AAS"

    display_name_text = {"en": f"{display_name}"}
    sm.display_name = model.MultiLanguageTextType(display_name_text)

    return sm


def create_base_ass(identifier: str, id_short: str, display_name: str = "", description: str = "") -> model.AssetAdministrationShell:
    """Create a basic AAS.

    :param identifier: identifier of the AAS
    :param id_short: ID short of the AAS
    :param display_name: display name of the AAS, defaults to ""
    :param description: description of the AAS, defaults to ""
    :return: AssetAdministrationShell instance
    """
    asset_info = create_base_asset_information(identifier)

    aas = model.AssetAdministrationShell(id_=asset_info.global_asset_id, asset_information=asset_info)
    aas.id_short = id_short

    if not description:
        description = f"This is the asset administration shell with ID short '{id_short}'"

    description_text = {"en": f"{description}"}
    aas.description = model.MultiLanguageTextType(description_text)

    if not display_name:
        display_name = "POC AAS"

    display_name_text = {"en": f"{display_name}"}
    aas.display_name = model.MultiLanguageTextType(display_name_text)

    return aas


def create_base_asset_information(identifier: str) -> model.AssetInformation:
    """Return a basic AssetInformation instance.

    :param id_short: short ID of the AssetInformation
    :param namespace: namespace of the AssetInformation, defaults to "basyx_python_aas_server"
    :return: AssetInformation instance
    """
    return model.AssetInformation(model.AssetKind.INSTANCE, identifier)


def create_reference(id: str) -> model.ModelReference:
    """Create a ModelReference.

    :param id: ID of the Submodel to reference
    :return: ModelReference instance
    """
    return model.ModelReference.from_referable(model.Submodel(id))
