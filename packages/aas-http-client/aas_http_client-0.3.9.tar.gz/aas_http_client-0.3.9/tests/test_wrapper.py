import pytest
from pathlib import Path
from aas_http_client.wrapper.sdk_wrapper import create_wrapper_by_config, SdkWrapper, create_wrapper_by_dict, create_wrapper_by_url
from basyx.aas import model
import aas_http_client.utilities.model_builder as model_builder
import aas_http_client.utilities.sdk_tools as sdk_tools
from urllib.parse import urlparse
import json

JAVA_SERVER_PORTS = [8075]
PYTHON_SERVER_PORTS = [8080, 80]
DOTNET_SERVER_PORTS = [5043]

CONFIG_FILES = [
    "./tests/server_configs/test_dotnet_server_config.yml",
    "./tests/server_configs/test_java_server_config.yml",
    "./tests/server_configs/test_python_server_config.yml"
]

# CONFIG_FILES = [
#     "./tests/server_configs/test_dotnet_server_config_local.json",
# ]

@pytest.fixture(params=CONFIG_FILES, scope="module")
def wrapper(request) -> SdkWrapper:
    try:
        file = Path(request.param).resolve()

        if not file.exists():
            raise FileNotFoundError(f"Configuration file {file} does not exist.")

        wrapper = create_wrapper_by_config(file, password="")
    except Exception as e:
        raise RuntimeError("Unable to connect to server.")

    shells = wrapper.get_all_asset_administration_shells()
    if shells is None:
        raise RuntimeError("No shells found on server. Please check the server configuration.")

    return wrapper

@pytest.fixture(scope="module")
def shared_sme_string() -> model.Property:
    # create a Submodel
    return model_builder.create_base_submodel_element_property("sme_property_string", model.datatypes.String, "Sample String Value")

@pytest.fixture(scope="module")
def shared_sme_bool() -> model.Property:
    # create a Submodel
    return model_builder.create_base_submodel_element_property("sme_property_bool", model.datatypes.Boolean, True)

@pytest.fixture(scope="module")
def shared_sme_int() -> model.Property:
    # create a Submodel
    return model_builder.create_base_submodel_element_property("sme_property_int", model.datatypes.Integer, 262)

@pytest.fixture(scope="module")
def shared_sme_float() -> model.Property:
    # create a Submodel
    return model_builder.create_base_submodel_element_property("sme_property_float", model.datatypes.Float, 262.3)

@pytest.fixture(scope="module")
def shared_sm() -> model.Submodel:
    # create a Submodel
    submodel = model_builder.create_base_submodel(identifier="fluid40/sm_http_client_unit_tests", id_short="sm_http_client_unit_tests")
    submodel.category = "Unit Test"
    return submodel

@pytest.fixture(scope="module")
def shared_aas(shared_sm: model.Submodel) -> model.AssetAdministrationShell:
    # create an AAS
    aas = model_builder.create_base_ass(identifier="fluid40/aas_http_client_unit_tests", id_short="aas_http_client_unit_tests")

    # add Submodel to AAS
    sdk_tools.add_submodel_to_aas(aas, shared_sm)

    return aas

def test_000a_create_wrapper_by_url(wrapper: SdkWrapper):
    base_url: str = wrapper.base_url
    new_client: SdkWrapper = create_wrapper_by_url(base_url=base_url)
    assert new_client is not None

def test_000b_create_wrapper_by_dict(wrapper: SdkWrapper):
    base_url: str = wrapper.base_url

    config_dict: dict = {
        "base_url": base_url
    }

    new_client: SdkWrapper = create_wrapper_by_dict(configuration=config_dict)
    assert new_client is not None

def test_000c_get_client(wrapper: SdkWrapper):
    client = wrapper.get_client()
    assert client is not None
    root = client.get_root()
    assert root is not None

def test_001_connect(wrapper: SdkWrapper):
    assert wrapper is not None

def test_002_get_all_asset_administration_shells(wrapper: SdkWrapper):
    shells = wrapper.get_all_asset_administration_shells()
    assert shells is not None
    assert len(shells) == 0

def test_003_post_asset_administration_shell(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell):
    shell = wrapper.post_asset_administration_shell(shared_aas)

    assert shell is not None
    assert shell.id == shared_aas.id
    assert shell.id_short == shared_aas.id_short

    shells = wrapper.get_all_asset_administration_shells()
    assert shells is not None
    assert len(shells) == 1
    assert shells[0].id_short == shared_aas.id_short
    assert shells[0].id == shared_aas.id

def test_004a_get_asset_administration_shell_by_id(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell):
    shell = wrapper.get_asset_administration_shell_by_id(shared_aas.id)

    assert shell is not None
    assert shell.id_short == shared_aas.id_short
    assert shell.id == shared_aas.id

def test_004b_get_asset_administration_shell_by_id(wrapper: SdkWrapper):
    shell = wrapper.get_asset_administration_shell_by_id("non_existent_id")

    assert shell is None

def test_005a_put_asset_administration_shell_by_id(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell):
    aas = model.AssetAdministrationShell(id_=shared_aas.asset_information.global_asset_id, asset_information=shared_aas.asset_information)
    aas.id_short = shared_aas.id_short

    description_text = "Put description for unit tests"
    aas.description = model.MultiLanguageTextType({"en": description_text})
    aas.submodel = shared_aas.submodel  # Keep existing submodels

    result = wrapper.put_asset_administration_shell_by_id(shared_aas.id, aas)

    assert result

    shell = wrapper.get_asset_administration_shell_by_id(shared_aas.id)

    assert shell is not None
    assert shell.id_short == shared_aas.id_short
    assert shell.id == shared_aas.id
    # description must have changed
    assert shell.description.get("en", "") == description_text
    assert shell.description.get("en", "") != shared_aas.description.get("en", "")
    # submodels must be retained
    assert len(shell.submodel) == len(shared_aas.submodel)

    # The display name must be empty
    # currently not working in dotnet
    # assert len(get_result.get("displayName", {})) == 0

    # # restore to its original state
    wrapper.put_asset_administration_shell_by_id(shared_aas.id, shared_aas)  # Restore original submodel

def test_005b_put_asset_administration_shell_by_id(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell):
    # put with other ID
    id_short = "put_short_id"
    identifier = f"fluid40/{id_short}"
    asset_info = model_builder.create_base_asset_information(identifier)
    aas = model.AssetAdministrationShell(id_=asset_info.global_asset_id, asset_information=asset_info)
    aas.id_short = id_short

    description_text = {"en": "Updated description for unit tests"}
    aas.description = model.MultiLanguageTextType(description_text)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in PYTHON_SERVER_PORTS:
        # NOTE: Python server crashes by this test
        result = False
    else:
        result = wrapper.put_asset_administration_shell_by_id(shared_aas.id, aas)

    assert not result

    assert not result

    shell = wrapper.get_asset_administration_shell_by_id(shared_aas.id)

    assert shell.description.get("en", "") != description_text
    assert shell.description.get("en", "") == shared_aas.description.get("en", "")

def test_006_get_asset_administration_shell_by_id_reference_aas_repository(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell):
    reference = wrapper.get_asset_administration_shell_by_id_reference_aas_repository(shared_aas.id)

    assert reference is not None
    assert len(reference.key) == 1
    assert reference.key[0].value == shared_aas.id

def test_007_get_submodel_by_id_aas_repository(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell, shared_sm: model.Submodel):
    submodel = wrapper.get_submodel_by_id_aas_repository(shared_aas.id, shared_sm.id)

    assert submodel is None

def test_008_get_all_submodels(wrapper: SdkWrapper):
    submodels = wrapper.get_all_submodels()
    assert submodels is not None
    assert len(submodels) == 0

def test_009_post_submodel(wrapper: SdkWrapper, shared_sm: model.Submodel):
    submodel = wrapper.post_submodel(shared_sm)

    assert submodel is not None
    assert submodel.id == shared_sm.id
    assert submodel.id_short == shared_sm.id_short

    submodels = wrapper.get_all_submodels()
    assert submodels is not None
    assert len(submodels) == 1
    assert submodels[0].id_short == shared_sm.id_short
    assert submodels[0].id == shared_sm.id

def test_010_get_submodel_by_id_aas_repository(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell, shared_sm: model.Submodel):
    submodel = wrapper.get_submodel_by_id_aas_repository(shared_aas.id, shared_sm.id)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in JAVA_SERVER_PORTS:
        # Basyx java server do not provide this endpoint
        assert submodel is None
    else:
        assert submodel is not None
        assert submodel.id_short == shared_sm.id_short
        assert submodel.id == shared_sm.id

def test_011a_get_submodel_by_id(wrapper: SdkWrapper, shared_sm: model.Submodel):
    submodel = wrapper.get_submodel_by_id(shared_sm.id)

    assert submodel is not None
    assert submodel.id_short == shared_sm.id_short
    assert submodel.id == shared_sm.id

def test_011b_get_submodel_by_id(wrapper: SdkWrapper):
    result = wrapper.get_submodel_by_id("non_existent_id")

    assert result is None

def test_012_patch_submodel_by_id(wrapper: SdkWrapper, shared_sm: model.Submodel):
    sm = model.Submodel(shared_sm.id_short)
    sm.id_short = shared_sm.id_short

    description_text = "Patched description for unit tests"
    sm.description = model.MultiLanguageTextType({"en": description_text})

    result = wrapper.patch_submodel_by_id(shared_sm.id, sm)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in JAVA_SERVER_PORTS or int(parsed.port) in PYTHON_SERVER_PORTS:
        # Basyx java server do not provide this endpoint
        assert not result
    else:
        assert result

        submodel = wrapper.get_submodel_by_id(shared_sm.id)
        assert submodel is not None
        assert submodel.id_short == shared_sm.id_short
        assert submodel.id == shared_sm.id
        # Only the description may change in patch.
        assert submodel.description.get("en", "") == description_text
        assert submodel.description.get("en", "") != shared_sm.description.get("en", "")
        # The display name must remain the same.
        assert submodel.display_name == shared_sm.display_name
        assert len(submodel.submodel_element) == len(shared_sm.submodel_element)

def test_013_put_submodel_by_id_aas_repository(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell, shared_sm: model.Submodel):
    sm = model.Submodel(shared_sm.id)
    sm.id_short = shared_sm.id_short

    description_text = "Put via shell description for unit tests"
    sm.description = model.MultiLanguageTextType({"en": description_text})
    sm.display_name = shared_sm.display_name  # Keep existing display name because of problems with empty lists

    result = wrapper.put_submodel_by_id_aas_repository(shared_aas.id, shared_sm.id, sm)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in JAVA_SERVER_PORTS:
        # Basyx java server do not provide this endpoint
        assert not result
    else:
        assert result

        submodel = wrapper.get_submodel_by_id_aas_repository(shared_aas.id, shared_sm.id)
        assert submodel is not None
        assert submodel.id_short == shared_sm.id_short
        assert submodel.id == shared_sm.id
        # description must have changed
        assert submodel.description.get("en", "") == description_text
        assert submodel.description.get("en", "") != shared_sm.description.get("en", "")
        # display name stays
        assert submodel.display_name == shared_sm.display_name
        # category was not set an must be empty
        assert submodel.category is None
        assert len(submodel.submodel_element) == 0

        # restore to its original state
        wrapper.put_submodel_by_id_aas_repository(shared_aas.id, shared_sm.id, shared_sm)  # Restore original submodel

def test_014_put_submodels_by_id(wrapper: SdkWrapper, shared_sm: model.Submodel):
    sm = model.Submodel(shared_sm.id)
    sm.id_short = shared_sm.id_short

    description_text = "Put description for unit tests"
    sm.description = model.MultiLanguageTextType({"en": description_text})
    sm.display_name = shared_sm.display_name  # Keep existing display name because of problems with empty lists

    result = wrapper.put_submodels_by_id(shared_sm.id, sm)

    assert result

    submodel = wrapper.get_submodel_by_id(shared_sm.id)
    assert submodel is not None
    assert submodel.id_short == shared_sm.id_short
    assert submodel.id == shared_sm.id
    # description must have changed
    assert submodel.description.get("en", "") == description_text
    assert submodel.description.get("en", "") != shared_sm.description.get("en", "")
    # display name stays
    # assert submodel.display_name == shared_sm.display_name
    # category was not set an must be empty
    assert submodel.category is None
    assert len(submodel.submodel_element) == 0

    # restore to its original state
    wrapper.put_submodels_by_id(shared_sm.id, shared_sm)  # Restore original submodel

def test_015_get_all_submodel_elements_submodel_repository(wrapper: SdkWrapper, shared_sm: model.Submodel):
    submodel_elements = wrapper.get_all_submodel_elements_submodel_repository(shared_sm.id)

    assert submodel_elements is not None
    assert len(submodel_elements) == 0

def test_016a_post_submodel_element_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_string: model.Property):
    submodel_element = wrapper.post_submodel_element_submodel_repo(shared_sm.id, shared_sme_string)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)
    property: model.Property = submodel_element
    assert property.value == shared_sme_string.value

    assert submodel_element.id_short == shared_sme_string.id_short
    assert submodel_element.description.get("en", "") == shared_sme_string.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_string.display_name.get("en", "")
    assert submodel_element.value == shared_sme_string.value

    submodel_elements = wrapper.get_all_submodel_elements_submodel_repository(shared_sm.id)

    assert submodel_elements is not None
    assert len(submodel_elements) == 1

def test_016b_post_submodel_element_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_bool: model.Property):
    submodel_element = wrapper.post_submodel_element_submodel_repo(shared_sm.id, shared_sme_bool)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)
    property: model.Property = submodel_element
    assert property.value == shared_sme_bool.value

    assert submodel_element.id_short == shared_sme_bool.id_short
    assert submodel_element.description.get("en", "") == shared_sme_bool.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_bool.display_name.get("en", "")
    assert submodel_element.value == shared_sme_bool.value

    submodel_elements = wrapper.get_all_submodel_elements_submodel_repository(shared_sm.id)

    assert submodel_elements is not None
    assert len(submodel_elements) == 2

def test_016c_post_submodel_element_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_int: model.Property):
    submodel_element = wrapper.post_submodel_element_submodel_repo(shared_sm.id, shared_sme_int)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)
    property: model.Property = submodel_element
    assert property.value == shared_sme_int.value

    assert submodel_element.id_short == shared_sme_int.id_short
    assert submodel_element.description.get("en", "") == shared_sme_int.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_int.display_name.get("en", "")
    assert submodel_element.value == shared_sme_int.value

    submodel_elements = wrapper.get_all_submodel_elements_submodel_repository(shared_sm.id)

    assert submodel_elements is not None
    assert len(submodel_elements) == 3

def test_016d_post_submodel_element_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_float: model.Property):
    submodel_element = wrapper.post_submodel_element_submodel_repo(shared_sm.id, shared_sme_float)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)
    property: model.Property = submodel_element
    assert property.value == shared_sme_float.value

    assert submodel_element.id_short == shared_sme_float.id_short
    assert submodel_element.description.get("en", "") == shared_sme_float.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_float.display_name.get("en", "")
    assert submodel_element.value == shared_sme_float.value

    submodel_elements = wrapper.get_all_submodel_elements_submodel_repository(shared_sm.id)

    assert submodel_elements is not None
    assert len(submodel_elements) == 4

def test_017a_get_submodel_element_by_path_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_string: model.Property):
    submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_string.id_short)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)

    assert submodel_element.id_short == shared_sme_string.id_short
    assert submodel_element.description.get("en", "") == shared_sme_string.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_string.display_name.get("en", "")
    assert submodel_element.value == shared_sme_string.value

def test_017b_get_submodel_element_by_path_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_bool: model.Property):
    submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_bool.id_short)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)

    assert submodel_element.id_short == shared_sme_bool.id_short
    assert submodel_element.description.get("en", "") == shared_sme_bool.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_bool.display_name.get("en", "")
    assert submodel_element.value == shared_sme_bool.value

def test_017c_get_submodel_element_by_path_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_int: model.Property):
    submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_int.id_short)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)

    assert submodel_element.id_short == shared_sme_int.id_short
    assert submodel_element.description.get("en", "") == shared_sme_int.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_int.display_name.get("en", "")
    assert submodel_element.value == shared_sme_int.value

def test_017d_get_submodel_element_by_path_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_float: model.Property):
    submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_float.id_short)

    assert submodel_element is not None

    assert isinstance(submodel_element, model.Property)

    assert submodel_element.id_short == shared_sme_float.id_short
    assert submodel_element.description.get("en", "") == shared_sme_float.description.get("en", "")
    assert submodel_element.display_name.get("en", "") == shared_sme_float.display_name.get("en", "")
    assert submodel_element.value == shared_sme_float.value

def test_018a_patch_submodel_element_by_path_value_only_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_string: model.Property):
    new_value = "Patched String Value"
    result = wrapper.patch_submodel_element_by_path_value_only_submodel_repo(shared_sm.id, shared_sme_string.id_short, new_value)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in PYTHON_SERVER_PORTS:
        # NOTE: python server do not provide this endpoint
        assert result is False
    else:
        assert result is True

        submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_string.id_short)

        assert submodel_element is not None
        assert submodel_element.id_short == shared_sme_string.id_short
        assert submodel_element.description.get("en", "") == shared_sme_string.description.get("en", "")
        assert submodel_element.display_name.get("en", "") == shared_sme_string.display_name.get("en", "")

        assert isinstance(submodel_element, model.Property)
        property: model.Property = submodel_element
        assert property.value == new_value

def test_018b_patch_submodel_element_by_path_value_only_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_bool: model.Property):
    new_value = "false"
    result = wrapper.patch_submodel_element_by_path_value_only_submodel_repo(shared_sm.id, shared_sme_bool.id_short, new_value)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in PYTHON_SERVER_PORTS:
        # NOTE: python server do not provide this endpoint
        assert result is False
    else:
        assert result is True

        submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_bool.id_short)

        assert submodel_element is not None
        assert submodel_element.id_short == shared_sme_bool.id_short
        assert submodel_element.description.get("en", "") == shared_sme_bool.description.get("en", "")
        assert submodel_element.display_name.get("en", "") == shared_sme_bool.display_name.get("en", "")

        assert isinstance(submodel_element, model.Property)
        property: model.Property = submodel_element
        assert property.value == json.loads(new_value)

def test_018c_patch_submodel_element_by_path_value_only_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_int: model.Property):
    new_value = "263"
    result = wrapper.patch_submodel_element_by_path_value_only_submodel_repo(shared_sm.id, shared_sme_int.id_short, new_value)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in PYTHON_SERVER_PORTS:
        # NOTE: python server do not provide this endpoint
        assert result is False
    else:
        assert result is True

        submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_int.id_short)

        assert submodel_element is not None
        assert submodel_element.id_short == shared_sme_int.id_short
        assert submodel_element.description.get("en", "") == shared_sme_int.description.get("en", "")
        assert submodel_element.display_name.get("en", "") == shared_sme_int.display_name.get("en", "")

        assert isinstance(submodel_element, model.Property)
        property: model.Property = submodel_element
        assert property.value == int(new_value)

def test_018d_patch_submodel_element_by_path_value_only_submodel_repo(wrapper: SdkWrapper, shared_sm: model.Submodel, shared_sme_float: model.Property):
    new_value = "262.1"
    result = wrapper.patch_submodel_element_by_path_value_only_submodel_repo(shared_sm.id, shared_sme_float.id_short, new_value)

    parsed = urlparse(wrapper.base_url)
    if int(parsed.port) in PYTHON_SERVER_PORTS:
        # NOTE: python server do not provide this endpoint
        assert result is False
    else:
        assert result is True

        submodel_element = wrapper.get_submodel_element_by_path_submodel_repo(shared_sm.id, shared_sme_float.id_short)

        assert submodel_element is not None
        assert submodel_element.id_short == shared_sme_float.id_short
        assert submodel_element.description.get("en", "") == shared_sme_float.description.get("en", "")
        assert submodel_element.display_name.get("en", "") == shared_sme_float.display_name.get("en", "")

        assert isinstance(submodel_element, model.Property)
        property: model.Property = submodel_element
        assert property.value == float(new_value)

def test_098_delete_asset_administration_shell_by_id(wrapper: SdkWrapper, shared_aas: model.AssetAdministrationShell):
    result = wrapper.delete_asset_administration_shell_by_id(shared_aas.id)

    assert result

    shells = wrapper.get_all_asset_administration_shells()
    assert shells is not None
    assert len(shells) == 0

def test_099_delete_submodel_by_id(wrapper: SdkWrapper, shared_sm: model.Submodel):
    result = wrapper.delete_submodel_by_id(shared_sm.id)

    assert result

    submodels = wrapper.get_all_submodels()
    assert submodels is not None
    assert len(submodels) == 0
