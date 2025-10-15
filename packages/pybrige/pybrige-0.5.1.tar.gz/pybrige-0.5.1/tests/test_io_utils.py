import gzip
import json
import io
import pytest
from pybrige.utils.io import (
    atomic_write_text,
    atomic_write_bytes,
    backup_file,
    write_json,
    read_json,
    iter_json_lines,
    append_json_line,
    stream_jsonl,
    count_file_lines,
)
from pybrige import parse_csv
# --- Testes para Gzip ---
@pytest.mark.parametrize("filename", ["test.json", "test.json.gz"])
def test_gzip_integration_for_json_and_jsonl(tmp_path, filename):
    """Testa se as funções JSON e JSONL funcionam com e sem gzip."""
    file = tmp_path / filename
    data = {"hello": "world"}
    
    # 1. Testa write_json e read_json
    write_json(file, data)
    read_data = read_json(file)
    assert read_data == data
    
    # 2. Testa append_json_line e iter_json_lines
    append_json_line(file, data)
    records = list(iter_json_lines(file))
    # O ficheiro agora terá o JSON original + a linha JSONL, pode não ser válido
    # Vamos criar um novo para um teste limpo de JSONL
    jsonl_file = tmp_path / f"data.{'jsonl.gz' if filename.endswith('.gz') else 'jsonl'}"
    append_json_line(jsonl_file, {"id": 1})
    append_json_line(jsonl_file, {"id": 2})
    records = list(iter_json_lines(jsonl_file))
    assert records == [{"id": 1}, {"id": 2}]

def test_count_file_lines_with_gzip(tmp_path):
    """Testa a contagem de linhas para ficheiros normais e .gz."""
    plain_file = tmp_path / "plain.txt"
    gz_file = tmp_path / "compressed.txt.gz"
    content = "line 1\nline 2\nline 3"

    plain_file.write_text(content)
    with gzip.open(gz_file, "wt") as f:
        f.write(content)
        
    assert count_file_lines(plain_file) == 3
    assert count_file_lines(gz_file) == 3

# --- Testes para Backup e Atomic Writes ---
def test_atomic_write_bytes(tmp_path):
    """Testa a escrita atómica de bytes."""
    file = tmp_path / "binary.dat"
    data = b"\x01\x02\x03"
    atomic_write_bytes(file, data)
    assert file.read_bytes() == data

def test_backup_file(tmp_path):
    """Testa a lógica de backup rotativo."""
    file = tmp_path / "config.ini"
    file.write_text("v1")
    
    # Primeiro backup: config.ini -> config.ini.bak.1
    backup_file(file, keep=2)
    bak1 = tmp_path / "config.ini.bak.1"
    assert not file.exists()
    assert bak1.exists()
    assert bak1.read_text() == "v1"

    # Segundo backup: config.ini.bak.1 -> .bak.2, config.ini -> .bak.1
    file.write_text("v2")
    backup_file(file, keep=2)
    bak2 = tmp_path / "config.ini.bak.2"
    assert not file.exists()
    assert bak1.read_text() == "v2" # Novo .bak.1
    assert bak2.exists()
    assert bak2.read_text() == "v1" # Antigo .bak.1 virou .bak.2
    
    # Terceiro backup: .bak.2 é apagado porque keep=2
    file.write_text("v3")
    backup_file(file, keep=2)
    assert bak1.read_text() == "v3"
    assert bak2.read_text() == "v2"
    assert not (tmp_path / "config.ini.bak.3").exists()

# --- Teste para Streaming ---
def test_stream_jsonl(tmp_path):
    """Testa a escrita de um iterador para um ficheiro e para um stream em memória."""
    records = ({"id": i} for i in range(3)) # Um gerador, para testar a eficiência de memória
    
    # 1. Testa escrita para ficheiro
    file = tmp_path / "stream.jsonl"
    stream_jsonl(records, file)
    
    read_back = list(iter_json_lines(file))
    assert read_back == [{"id": 0}, {"id": 1}, {"id": 2}]
    
    # 2. Testa escrita para stream em memória (StringIO)
    string_io = io.StringIO()
    records = ({"id": i} for i in range(2)) # Reinicia o gerador
    stream_jsonl(records, string_io)
    
    output = string_io.getvalue().strip().split('\n')
    assert len(output) == 2
import os
import io
import gzip
import json
import pytest
from pathlib import Path
from pybrige.utils.io import (
    atomic_write_text,
    atomic_write_bytes,
    write_json,
    read_json,
    append_json_line,
    iter_json_lines,
    read_json_lines,
    tail_json_lines,
    stream_jsonl,
    count_file_lines,
    merge_json_files,
    validate_json,
    backup_file,
)

# ------------------------
# Atomic writes
# ------------------------
def test_atomic_write_text_and_bytes(tmp_path):
    txt = tmp_path / "file.txt"
    atomic_write_text(txt, "hello world")
    assert txt.read_text("utf-8") == "hello world"

    binf = tmp_path / "file.bin"
    atomic_write_bytes(binf, b"010101")
    assert binf.read_bytes() == b"010101"


# ------------------------
# JSON read/write
# ------------------------
def test_write_and_read_json(tmp_path):
    f = tmp_path / "data.json"
    data = {"a": 1, "b": [1, 2, 3]}
    write_json(f, data)
    loaded = read_json(f)
    assert loaded == data

def test_write_json_gzip_and_read(tmp_path):
    f = tmp_path / "compressed.json.gz"
    data = {"msg": "gzip"}
    write_json(f, data, gzip_out=True)
    loaded = read_json(f)
    assert loaded == data
    assert f.suffix == ".gz"

def test_read_json_safe_on_missing(tmp_path):
    f = tmp_path / "missing.json"
    assert read_json(f, safe=True, default={"x": 1}) == {"x": 1}
    with pytest.raises(FileNotFoundError):
        read_json(f, safe=False)


# ------------------------
# JSON Lines
# ------------------------
def test_append_and_iter_json_lines(tmp_path):
    f = tmp_path / "events.jsonl"
    append_json_line(f, {"id": 1})
    append_json_line(f, {"id": 2})
    recs = list(iter_json_lines(f))
    assert recs == [{"id": 1}, {"id": 2}]
    assert read_json_lines(f) == recs

def test_tail_json_lines(tmp_path):
    f = tmp_path / "events.jsonl"
    for i in range(5):
        append_json_line(f, {"i": i})
    last2 = tail_json_lines(f, 2)
    assert last2 == [{"i": 3}, {"i": 4}]
    assert tail_json_lines(f, 0) == []


# ------------------------
# Stream JSONL
# ------------------------
def test_stream_jsonl_to_file_and_filelike(tmp_path):
    f = tmp_path / "out.jsonl"
    records = [{"n": i} for i in range(3)]
    stream_jsonl(records, f)
    loaded = read_json_lines(f)
    assert loaded == records

    buf = io.StringIO()
    stream_jsonl(records, buf, atomic=False)
    buf.seek(0)
    lines = [json.loads(l) for l in buf.readlines()]
    assert lines == records


# ------------------------
# Count file lines
# ------------------------
def test_count_file_lines_normal_and_gzip(tmp_path):
    f = tmp_path / "lines.txt"
    f.write_text("a\nb\nc\n")
    assert count_file_lines(f) == 3

    g = tmp_path / "lines.txt.gz"
    with gzip.open(g, "wt", encoding="utf-8") as gf:
        gf.write("1\n2\n3\n")
    assert count_file_lines(g) == 3

    missing = tmp_path / "no.txt"
    assert count_file_lines(missing) == 0


# ------------------------
# Merge JSON Files
# ------------------------
def test_merge_json_files_array(tmp_path):
    f1 = tmp_path / "a.json"
    f2 = tmp_path / "b.json"
    write_json(f1, {"x": 1})
    write_json(f2, [2, 3])
    dest = tmp_path / "merged.json"
    merge_json_files([f1, f2], dest, mode="array")
    result = read_json(dest)
    assert result == [{"x": 1}, [2, 3]]

def test_merge_json_files_lines(tmp_path):
    f1 = tmp_path / "l1.jsonl"
    f2 = tmp_path / "l2.jsonl"
    append_json_line(f1, {"id": 1})
    append_json_line(f2, {"id": 2})
    dest = tmp_path / "dest.jsonl"
    merge_json_files([f1, f2], dest, mode="lines")
    lines = list(iter_json_lines(dest))
    assert {"id": 1} in lines and {"id": 2} in lines

def test_merge_json_files_invalid_mode(tmp_path):
    f = tmp_path / "a.json"
    write_json(f, {"x": 1})
    dest = tmp_path / "bad.json"
    with pytest.raises(ValueError):
        merge_json_files([f], dest, mode="oops")


# ------------------------
# Validate JSON
# ------------------------
def test_validate_json_with_schema_and_predicate():
    schema = {"required": ["user", "id"]}
    assert validate_json({"user": "a", "id": 1}, schema=schema)
    assert not validate_json({"user": "a"}, schema=schema)

    pred = lambda d: isinstance(d, dict) and d.get("ok", False)
    assert validate_json({"ok": True}, predicate=pred)
    assert not validate_json({"ok": False}, predicate=pred)
    assert not validate_json("string", predicate=pred)


# ------------------------
# Backup
# ------------------------
def test_backup_file(tmp_path):
    f = tmp_path / "data.json"
    write_json(f, {"v": 1}, atomic=False)
    backup_file(f, keep=3)
    # Agora existe .bak.1
    assert any("bak.1" in x.name for x in tmp_path.iterdir())



def test_parse_csv():
    assert parse_csv("1;2;3") == [1, 2, 3]
    assert parse_csv(" 4 ; 5 ; 6 ") == [4, 5, 6]
    assert parse_csv("") == []