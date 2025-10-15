import re
from pathlib import Path

# Raízes do projeto para varrer
ROOTS = [Path("src/pybrige"), Path("tests")]

# Padrões a substituir
REPLACEMENTS = {
    r"\blist\[(.*?)\]": r"List[\1]",
    r"\bdict\[(.*?)\]": r"Dict[\1]",
    r"\btuple\[(.*?)\]": r"Tuple[\1]",
    r"\bset\[(.*?)\]": r"Set[\1]",
}

def ensure_typing_imports(content: str) -> str:
    """Garante que Dict, List, Tuple, Set, Optional estão importados de typing."""
    if "from typing import" not in content:
        return "from typing import Dict, List, Tuple, Set, Optional\n" + content
    
    needed = ["Dict", "List", "Tuple", "Set", "Optional"]
    for n in needed:
        if n not in content:
            content = content.replace("from typing import", f"from typing import {n},")
    return content


def fix_optional_union(text: str) -> str:
    """
    Converte 'str | None' → 'Optional[str]', 'Dict[str, Any] | None' → 'Optional[Dict[str, Any]]'
    """
    # Captura qualquer padrão T | None ou None | T
    pattern = re.compile(r"([\w\[\], ]+)\s*\|\s*None")
    text = pattern.sub(r"Optional[\1]", text)
    pattern = re.compile(r"None\s*\|\s*([\w\[\], ]+)")
    text = pattern.sub(r"Optional[\1]", text)
    return text


def patch_file(file_path: Path) -> bool:
    text = file_path.read_text(encoding="utf-8")
    original = text

    # Substituições básicas list/dict/tuple/set
    for pat, repl in REPLACEMENTS.items():
        text = re.sub(pat, repl, text)

    # Converte unions modernos para Optional
    text = fix_optional_union(text)

    # Garantir imports de typing
    if text != original:
        text = ensure_typing_imports(text)
        file_path.write_text(text, encoding="utf-8")
        print(f"[OK] Corrigido: {file_path}")
        return True
    return False


def main():
    changed = 0
    for root in ROOTS:
        if not root.exists():
            continue
        for py_file in root.rglob("*.py"):
            if patch_file(py_file):
                changed += 1
    print(f"\n✅ Concluído! Arquivos modificados: {changed}")


if __name__ == "__main__":
    main()
