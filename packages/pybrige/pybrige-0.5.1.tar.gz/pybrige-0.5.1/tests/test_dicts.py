import pytest
from pybrige.utils.dicts import (
    safe_get,
    deep_get,
    deep_set,
    merge_dicts,
    flatten_dict,
    unflatten_dict,
    dict_diff,
    filter_dict,
    invert_dict,
    update_if,
)

@pytest.fixture
def sample_nested_dict():
    """Fornece um dicionário aninhado de teste."""
    return {
        "user": {
            "profile": {"name": "ana", "age": 30},
            "roles": ["admin", "editor"],
        },
        "version": 1,
    }

def test_deep_get(sample_nested_dict):
    assert deep_get(sample_nested_dict, "user.profile.name") == "ana"
    assert deep_get(sample_nested_dict, "user.roles") == ["admin", "editor"]
    assert deep_get(sample_nested_dict, "user.profile.email") is None
    assert deep_get(sample_nested_dict, "user.profile.email", default="N/A") == "N/A"

def test_deep_set():
    d = {}
    deep_set(d, "a.b.c", 100)
    assert d == {"a": {"b": {"c": 100}}}
    deep_set(d, "a.b.d", 200)
    assert d == {"a": {"b": {"c": 100, "d": 200}}}
    deep_set(d, "a.x", 300)
    assert d == {"a": {"b": {"c": 100, "d": 200}, "x": 300}}

def test_merge_dicts():
    d1 = {"a": 1, "b": {"x": 10, "y": 20}}
    d2 = {"c": 3, "b": {"y": 25, "z": 30}}
    
    # Teste de fusão superficial
    shallow = merge_dicts(d1, d2, deep=False)
    assert shallow == {"a": 1, "c": 3, "b": {"y": 25, "z": 30}}

    # Teste de fusão profunda
    deep = merge_dicts(d1, d2, deep=True)
    assert deep == {"a": 1, "c": 3, "b": {"x": 10, "y": 25, "z": 30}}

def test_flatten_and_unflatten_dict(sample_nested_dict):
    flattened = flatten_dict(sample_nested_dict)
    expected_flattened = {
        "user.profile.name": "ana",
        "user.profile.age": 30,
        "user.roles": ["admin", "editor"],
        "user.active": True, # Supondo que adicionamos este campo
        "version": 1,
    }
    # Adicionando a chave 'active' ao sample_nested_dict para o teste
    sample_nested_dict["user"]["active"] = True

    # Recalculando o flattened com a nova chave
    flattened = flatten_dict(sample_nested_dict)
    assert flattened == expected_flattened

    # Testa o ciclo completo
    unflattened = unflatten_dict(flattened)
    assert unflattened == sample_nested_dict

def test_dict_diff():
    d1 = {"a": 1, "b": 2, "c": 3}
    d2 = {"b": 20, "c": 3, "d": 4}
    diff = dict_diff(d1, d2)
    assert diff["keys_add"] == ["d"]
    assert diff["keys_removed"] == ["a"]
    assert diff["changed"] == {"b": (2, 20)}

def test_filter_dict():
    d = {"a": 1, "b": 2, "c": 3, "d": 4}
    # Filtra apenas valores pares
    filtered = filter_dict(d, lambda k, v: v % 2 == 0)
    assert filtered == {"b": 2, "d": 4}

def test_invert_dict():
    d = {"a": 1, "b": 2}
    inverted = invert_dict(d)
    assert inverted == {1: "a", 2: "b"}

def test_update_if():
    d = {"count": 5, "name": "test"}
    # Incrementa 'count'
    update_if(d, "count", lambda x: x + 1)
    assert d["count"] == 6
    # Tenta atualizar chave inexistente (não deve fazer nada)
    update_if(d, "missing_key", lambda x: x + 1)
    assert "missing_key" not in d

def test_safe_get_existing_and_missing():
    d = {"a": 1, "b": None}

    # Chave existente
    assert safe_get(d, "a") == 1

    # Chave existente mas valor None
    assert safe_get(d, "b", default="x") is None  # Não sobrescreve None

    # Chave inexistente
    assert safe_get(d, "c", default=42) == 42    