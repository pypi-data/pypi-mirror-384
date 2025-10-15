from __future__ import annotations

from typing import Set, Any, Dict, Iterable, Mapping, MutableMapping, Callable, Union


def safe_get(d: Mapping[str, Any], key: str, default: Any = None) -> Any:
    """Obtém valor de forma segura, retornando `default` se não existir."""
    return d.get(key, default)


def deep_get(d: Mapping[str, Any], path: Union[str, Iterable[str]], default: Any = None) -> Any:
    """
    Busca em dicionário aninhado usando caminho (string 'a.b.c' ou lista ['a','b','c']).
    """
    if isinstance(path, str):
        path = path.split(".")
    current: Any = d
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    return current


def deep_set(d: MutableMapping[str, Any], path: Union[str, Iterable[str]], value: Any) -> None:
    """
    Define valor em dicionário aninhado criando chaves intermediárias se necessário.
    """
    if isinstance(path, str):
        path = path.split(".")
    current: MutableMapping[str, Any] = d
    for key in path[:-1]:
        if key not in current or not isinstance(current[key], MutableMapping):
            current[key] = {}
        current = current[key]
    current[path[-1]] = value


def merge_dicts(*dicts: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """
    Mescla múltiplos dicionários.
    - deep=True → recursivo (sub-dicts são mesclados em profundidade)
    - deep=False → sobrescreve no nível superficial
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        for k, v in d.items():
            if deep and isinstance(v, dict) and isinstance(result.get(k), dict):
                result[k] = merge_dicts(result[k], v, deep=True)
            else:
                result[k] = v
    return result


def flatten_dict(d: Mapping[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    "Achata" dicionário aninhado → chaves em formato 'a.b.c'
    """
    items: List[Tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, Mapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Mapping[str, Any], sep: str = ".") -> Dict[str, Any]:
    """
    Reverte flatten_dict → transforma 'a.b.c': x em dict aninhado.
    """
    result: Dict[str, Any] = {}
    for k, v in d.items():
        keys = k.split(sep)
        deep_set(result, keys, v)
    return result


def dict_diff(d1: Mapping[str, Any], d2: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Mostra diferenças entre dois dicionários:
    - keys_add: adicionadas
    - keys_removed: removidas
    - changed: valores alterados
    """
    diff = {
        "keys_add": [k for k in d2 if k not in d1],
        "keys_removed": [k for k in d1 if k not in d2],
        "changed": {k: (d1[k], d2[k]) for k in d1 if k in d2 and d1[k] != d2[k]},
    }
    return diff


def filter_dict(d: Mapping[str, Any], predicate: Callable[[str, Any], bool]) -> Dict[str, Any]:
    """Filtra dict com base em predicado key,value → bool."""
    return {k: v for k, v in d.items() if predicate(k, v)}


def invert_dict(d: Mapping[str, Any]) -> Dict[Any, str]:
    """Inverte chaves e valores (assume valores hashable e únicos)."""
    return {v: k for k, v in d.items()}


def update_if(d: MutableMapping[str, Any], key: str, func: Callable[[Any], Any]) -> None:
    """
    Atualiza valor de uma chave usando função transformadora, se existir.
    Exemplo:
        d = {"count": 2}
        update_if(d, "count", lambda x: x+1)
        -> d == {"count": 3}
    """
    if key in d:
        d[key] = func(d[key])
