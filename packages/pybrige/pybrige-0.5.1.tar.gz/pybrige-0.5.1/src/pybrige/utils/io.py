from __future__ import annotations

# src/pybrige/utils/io.py

import gzip
import io
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Set, Tuple, Any, Callable, Iterator, List, Optional, Sequence, Union, Dict
from typing import Set, Tuple, List



DEFAULT_ENCODING = "utf-8"
JsonObj = Union[dict, list]


# -------------------------
# Helpers de path / io
# -------------------------

def parse_csv(value: str) -> List[int]:
    """Converte uma string separada por ';' em uma lista de inteiros."""
    return [int(x.strip()) for x in value.split(";") if x.strip()]


def write_json_gz(file_path: str, data: Union[dict, list], indent: int = 4) -> None:
    """Escreve dados JSON em um arquivo gzipado."""
    with gzip.open(file_path, "wt", encoding=DEFAULT_ENCODING) as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

def read_json_gz(file_path: str) -> Any:
    """Lê dados JSON de um arquivo gzipado."""
    with gzip.open(file_path, "rt", encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


def _to_path(p: Union[str, os.PathLike, Path]) -> Path:
    return p if isinstance(p, Path) else Path(p)

def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def _open_maybe_gzip(path: Path, mode: str, encoding: str = DEFAULT_ENCODING):
    """
    Abstrai open para arquivos .gz (gzip) e normais. Mode deve ser 'rt','wt','rb','wb'.
    """
    if path.suffix == ".gz":
        # gzip.open accepts text mode 'rt' 'wt' with encoding param in py3.8+
        return gzip.open(path, mode=mode, encoding=encoding) if "t" in mode else gzip.open(path, mode=mode)
    return path.open(mode=mode, encoding=encoding) if "t" in mode else path.open(mode=mode)


# -------------------------
# Escrita atômica e backups
# -------------------------
def atomic_write_text(file_path: Union[str, os.PathLike, Path], text: str, encoding: str = DEFAULT_ENCODING) -> None:
    """
    Escreve texto de forma atômica: escreve num tempfile no mesmo diretório e faz os.replace.
    Compatível com caminhos .gz (gera arquivo .gz temporário e renomeia).
    """
    path = _to_path(file_path)
    _ensure_parent(path)

    # cria temp no mesmo diretório para garantir rename atômico
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=path.suffix)
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        if path.suffix == ".gz":
            # escrever bytes via gzip
            with gzip.open(tmp_path, "wt", encoding=encoding) as f:
                f.write(text)
        else:
            tmp_path.write_text(text, encoding=encoding)
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

def atomic_write_bytes(file_path: Union[str, os.PathLike, Path], data: bytes) -> None:
    """
    Versão para bytes (útil para binários).
    """
    path = _to_path(file_path)
    _ensure_parent(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=path.suffix)
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        tmp_path.write_bytes(data)
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

def backup_file(file_path: Union[str, os.PathLike, Path], keep: int = 5) -> None:
    """
    Cria backup rotativo: file -> file.bak.N (N aumenta). Mantém `keep` backups.
    """
    path = _to_path(file_path)
    if not path.exists():
        return
    _ensure_parent(path)
    # shift existing backups
    for i in range(keep - 1, 0, -1):
        src = path.with_suffix(path.suffix + f".bak.{i}")
        dst = path.with_suffix(path.suffix + f".bak.{i+1}")
        if src.exists():
            try:
                os.replace(src, dst)
            except Exception:
                pass
    # create bak.1
    try:
        os.replace(str(path), str(path.with_suffix(path.suffix + ".bak.1")))
    except Exception:
        # fall back to copy + unlink
        shutil.copy2(str(path), str(path.with_suffix(path.suffix + ".bak.1")))
        try:
            path.unlink()
        except Exception:
            pass


# -------------------------
# JSON (arquivo único)
# -------------------------
def write_json(
    file_path: Union[str, os.PathLike, Path],
    data: JsonObj,
    indent: int = 4,
    encoding: str = DEFAULT_ENCODING,
    ensure_ascii: bool = False,
    atomic: bool = True,
    gzip_out: Optional[bool] = None,
) -> None:
    """
    Escreve um JSON no caminho. Se atomic=True usa escrita atômica.
    gzip_out: if True forces .gz even if path doesn't have .gz suffix.
    """
    path = _to_path(file_path)
    _ensure_parent(path)

    if gzip_out and path.suffix != ".gz":
        # rewrite path to .gz
        path = path.with_suffix(path.suffix + ".gz")

    text = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    if atomic:
        atomic_write_text(path, text, encoding=encoding)
        return

    # non-atomic
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding=encoding) as f:
            f.write(text)
    else:
        with path.open("w", encoding=encoding) as f:
            f.write(text)


def read_json(
    file_path: Union[str, os.PathLike, Path],
    encoding: str = DEFAULT_ENCODING,
    safe: bool = False,
    default: Any = None,
) -> Any:
    """
    Lê JSON de arquivo. Se safe=True, retorna `default` quando arquivo não existir ou JSON inválido.
    """
    path = _to_path(file_path)
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding=encoding) as f:
                return json.load(f)
        with path.open("r", encoding=encoding) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if safe:
            return default
        raise


# -------------------------
# JSON Lines (JSONL)
# -------------------------
def append_json_line(
    file_path: Union[str, os.PathLike, Path],
    record: Dict[str, Any],
    encoding: str = DEFAULT_ENCODING,
    ensure_ascii: bool = False,
) -> None:
    """
    Acrescenta uma linha JSON ao arquivo (JSONL). Cria diretórios quando necessário.
    """
    path = _to_path(file_path)
    _ensure_parent(path)
    line = json.dumps(record, ensure_ascii=ensure_ascii)
    # sempre escreve em modo text append
    if path.suffix == ".gz":
        with gzip.open(path, "at", encoding=encoding) as f:
            f.write(line + "\n")
    else:
        with path.open("a", encoding=encoding) as f:
            f.write(line + "\n")


def iter_json_lines(
    file_path: Union[str, os.PathLike, Path],
    encoding: str = DEFAULT_ENCODING,
    skip_invalid: bool = True,
) -> Iterator[Dict[str, Any]]:
    """
    Iterador para JSONL. Se skip_invalid=True ignora linhas inválidas.
    """
    path = _to_path(file_path)
    if not path.exists():
        return
        yield  # type: ignore[unreachable]
    if path.suffix == ".gz":
        f = gzip.open(path, "rt", encoding=encoding)
    else:
        f = path.open("r", encoding=encoding)
    with f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    yield obj
            except json.JSONDecodeError:
                if not skip_invalid:
                    raise


def read_json_lines(
    file_path: Union[str, os.PathLike, Path],
    encoding: str = DEFAULT_ENCODING,
    skip_invalid: bool = True,
) -> List[Dict[str, Any]]:
    return list(iter_json_lines(file_path, encoding=encoding, skip_invalid=skip_invalid))


def tail_json_lines(
    file_path: Union[str, os.PathLike, Path],
    n: int,
    encoding: str = DEFAULT_ENCODING,
) -> List[Dict[str, Any]]:
    """
    Retorna as últimas n linhas de um JSONL. Implementação simples e portável:
    carrega todas as linhas (mantém simplicidade e legibilidade).
    """
    if n <= 0:
        return []
    return read_json_lines(file_path, encoding=encoding, skip_invalid=True)[-n:]


# -------------------------
# Streams e utilitários
# -------------------------
def stream_jsonl(
    records: Iterable[Dict[str, Any]],
    out: Union[str, os.PathLike, Path, io.TextIOBase],
    encoding: str = DEFAULT_ENCODING,
    ensure_ascii: bool = False,
    atomic: bool = True,
) -> None:
    """
    Escreve um iterator de records (JSON-serializáveis) para um destino (caminho ou file-like) em JSONL.
    """
    if isinstance(out, (str, os.PathLike, Path)):
        out_path = _to_path(out)
        _ensure_parent(out_path)
        if atomic:
            fd, tmp = tempfile.mkstemp(dir=str(out_path.parent), prefix=".tmp_stream_", suffix=out_path.suffix)
            os.close(fd)
            tmp_path = Path(tmp)
            try:
                with tmp_path.open("w", encoding=encoding) as f:
                    for r in records:
                        f.write(json.dumps(r, ensure_ascii=ensure_ascii) + "\n")
                os.replace(str(tmp_path), str(out_path))
                return
            finally:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
        else:
            with out_path.open("a", encoding=encoding) as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=ensure_ascii) + "\n")
        return

    # out é file-like
    for r in records:
        out.write(json.dumps(r, ensure_ascii=ensure_ascii) + "\n")
    out.flush()


def count_file_lines(file_path: Union[str, os.PathLike, Path], encoding: str = DEFAULT_ENCODING) -> int:
    path = _to_path(file_path)
    if not path.exists():
        return 0
    # leitura eficiente por iterar linhas
    with _open_maybe_gzip(path, "rt", encoding=encoding) as f:
        return sum(1 for _ in f)


# -------------------------
# Mesclas e validações
# -------------------------
def merge_json_files(
    sources: Sequence[Union[str, os.PathLike, Path]],
    dest: Union[str, os.PathLike, Path],
    mode: str = "array",
    encoding: str = DEFAULT_ENCODING,
    atomic: bool = True,
) -> None:
    """
    Mescla vários arquivos JSON/JSONL em um destino.
    mode:
      - "array": lê cada fonte como JSON e grava uma lista agregada
      - "lines": lê cada fonte como JSONL e escreve JSONL. Se a fonte for
                 um JSON de objeto/lista único, trata-o como um único registo.
    """
    dest_path = _to_path(dest)
    _ensure_parent(dest_path)
    if mode not in {"array", "lines"}:
        raise ValueError("mode deve ser 'array' ou 'lines'")

    if mode == "array":
        out_list: List[Any] = []
        for src in sources:
            obj = read_json(src, encoding=encoding, safe=False)
            out_list.append(obj)
        write_json(dest_path, out_list, encoding=encoding, atomic=atomic)
        return

    # --- LÓGICA MELHORADA PARA O MODO "LINES" ---
    for src in sources:
        src_path = _to_path(src)
        try:
            # Tenta primeiro ler como um ficheiro JSONL completo
            records = read_json_lines(src_path, encoding=encoding, skip_invalid=False)
            for rec in records:
                append_json_line(dest_path, rec, encoding=encoding)
        except json.JSONDecodeError:
            # Se falhar, assume que é um único objeto JSON e trata-o como um registo
            try:
                single_obj = read_json(src_path, encoding=encoding, safe=False)
                if isinstance(single_obj, dict):
                    append_json_line(dest_path, single_obj, encoding=encoding)
            except (json.JSONDecodeError, FileNotFoundError):
                # Ignora ficheiros corrompidos ou não encontrados neste modo
                pass
def pretty_print_json(
    data: Any,
    indent: int = 4,
    ensure_ascii: bool = False,
) -> str:
    """
    Retorna uma string JSON formatada de forma legível.
    """
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)


def validate_json(
    data: Any,
    schema: Optional[Dict[str, Any]] = None,
    predicate: Optional[Callable[[Any], bool]] = None,
) -> bool:
    """
    Validação leve sem dependências:
      - schema: dict with key "required": List[str]
      - predicate: callable that returns bool
    """
    ok = True
    if schema and "required" in schema:
        required = schema["required"]
        if isinstance(data, dict):
            ok = all(k in data for k in required)
        else:
            ok = False
    if predicate:
        try:
            ok = bool(ok and predicate(data))
        except Exception:
            return False
    return bool(ok)
