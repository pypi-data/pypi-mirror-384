# tests/test_io_utils_extra.py
import os
import io
import gzip
import json
import pytest
from pathlib import Path

from pybrige.utils.io import (
    write_json_gz,
    read_json_gz,
    atomic_write_text,
    atomic_write_bytes,
    backup_file,
    write_json,
    read_json,
    append_json_line,
    iter_json_lines,
    stream_jsonl,
    count_file_lines,
    merge_json_files,
    validate_json,
)

# -------------------------
# GZIP JSON
# -------------------------
def test_write_and_read_json_gz(tmp_path):
    file = tmp_path / "data.json.gz"
    data = {"msg": "hello", "num": 123}
    write_json_gz(file, data)
    out = read_json_gz(file)
    assert out == data


# -------------------------
# Atomic write
# -------------------------
def test_atomic_write_text_and_bytes(tmp_path):
    file_txt = tmp_path / "atomic.txt"
    file_bin = tmp_path / "atomic.bin"

    atomic_write_text(file_txt, "segredo")
    assert file_txt.read_text(encoding="utf-8") == "segredo"

    atomic_write_bytes(file_bin, b"\x00\x01\x02")
    assert file_bin.read_bytes() == b"\x00\x01\x02"


# -------------------------
# Backup rotation
# -------------------------
def test_backup_file_rotation(tmp_path):
    file = tmp_path / "config.json"
    file.write_text("original")

    # cria vários backups
    for i in range(3):
        backup_file(file, keep=3)
        file.write_text(f"versao-{i}")

    # Deve existir .bak.1 e .bak.2
    bak1 = tmp_path / "config.json.bak.1"
    bak2 = tmp_path / "config.json.bak.2"
    assert bak1.exists()
    assert bak2.exists()


# -------------------------
# Safe read_json
# -------------------------
def test_read_json_safe_and_default(tmp_path):
    file = tmp_path / "nope.json"

    # não existe -> retorna default
    assert read_json(file, safe=True, default="fallback") == "fallback"

    # inválido
    bad = tmp_path / "bad.json"
    bad.write_text("not-json")
    assert read_json(bad, safe=True, default={}) == {}


# -------------------------
# stream_jsonl
# -------------------------
def test_stream_jsonl_atomic_and_nonatomic(tmp_path):
    file1 = tmp_path / "atomic.jsonl"
    file2 = tmp_path / "nonatomic.jsonl"

    records = [{"i": 1}, {"i": 2}]

    # atomic
    stream_jsonl(records, file1, atomic=True)
    out = list(iter_json_lines(file1))
    assert out == records

    # non-atomic append
    stream_jsonl(records, file2, atomic=False)
    stream_jsonl([{"i": 3}], file2, atomic=False)
    out2 = list(iter_json_lines(file2))
    assert out2 == [{"i": 1}, {"i": 2}, {"i": 3}]

    # file-like (StringIO)
    buf = io.StringIO()
    stream_jsonl(records, buf, atomic=False)
    buf.seek(0)
    lines = [json.loads(l) for l in buf.getvalue().splitlines()]
    assert lines == records


# -------------------------
# count_file_lines
# -------------------------
def test_count_file_lines_txt_and_gz(tmp_path):
    txt = tmp_path / "f.txt"
    gz = tmp_path / "f.txt.gz"

    txt.write_text("a\nb\nc\n", encoding="utf-8")
    with gzip.open(gz, "wt", encoding="utf-8") as f:
        f.write("1\n2\n3\n")

    assert count_file_lines(txt) == 3
    assert count_file_lines(gz) == 3


# -------------------------
# merge_json_files
# -------------------------
def test_merge_json_files_array_and_lines(tmp_path):
    f1 = tmp_path / "a.json"
    f2 = tmp_path / "b.json"
    dest_array = tmp_path / "merged.json"
    dest_lines = tmp_path / "merged.jsonl"

    write_json(f1, {"x": 1})
    write_json(f2, {"y": 2})

    # array mode
    merge_json_files([f1, f2], dest_array, mode="array")
    arr = read_json(dest_array)
    assert {"x": 1} in arr and {"y": 2} in arr

    # lines mode
    append_json_line(dest_lines, {"z": 9})
    merge_json_files([f1], dest_lines, mode="lines")
    out_lines = list(iter_json_lines(dest_lines))
    assert {"z": 9} in out_lines and {"x": 1} in out_lines

    # modo inválido
    with pytest.raises(ValueError):
        merge_json_files([f1], dest_array, mode="WRONG")


# -------------------------
# validate_json
# -------------------------
def test_validate_json_with_schema_and_predicate():
    schema = {"required": ["id", "user"]}
    data_ok = {"id": 1, "user": "alice"}
    data_bad = {"id": 1}

    assert validate_json(data_ok, schema=schema)
    assert not validate_json(data_bad, schema=schema)

    # predicate ok
    assert validate_json(data_ok, predicate=lambda d: d["id"] == 1)

    # predicate que levanta exceção -> False
    def bad_pred(d): raise RuntimeError("boom")
    assert not validate_json(data_ok, predicate=bad_pred)
