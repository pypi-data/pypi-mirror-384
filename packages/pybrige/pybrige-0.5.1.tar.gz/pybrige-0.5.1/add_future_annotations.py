import os
from pathlib import Path

ROOT = Path("src/pybrige")

def add_future_import(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Já existe?
    if any("from __future__ import annotations" in line for line in lines):
        return False

    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('"""'):
            # Caso tenha docstring no início, mantém até fechar
            new_lines.append(line)
            for j in range(1, len(lines)):
                new_lines.append(lines[j])
                if '"""' in lines[j] and j != 0:
                    # adiciona logo após a docstring
                    new_lines.append("from __future__ import annotations\n\n")
                    inserted = True
                    new_lines.extend(lines[j+1:])
                    break
            break
        else:
            # sem docstring → adiciona na primeira linha
            new_lines.append("from __future__ import annotations\n\n")
            new_lines.extend(lines)
            inserted = True
            break

    if inserted:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    return inserted


def main():
    changed = 0
    for py_file in ROOT.rglob("*.py"):
        if add_future_import(py_file):
            print(f"[OK] Inserido em {py_file}")
            changed += 1
    print(f"\n✅ Concluído! Arquivos modificados: {changed}")


if __name__ == "__main__":
    main()
