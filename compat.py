"""Stato «compatibilita-main» di una PR, ricavato dai suoi commenti."""
import re

CAN_WRITE = {"admin", "maintain", "write"}
BLOCKS = {
    "COMPATIBILITA-MAIN": ("commit", "aggiornato con main", "test eseguiti", "non verificato"),
    "EMERGENZA": ("commit", "motivo"),
}


def _blocks(body: str):
    """I blocchi presenti in un commento, come (tipo, campi)."""
    kind, fields = None, {}
    for raw in (body or "").splitlines():
        line = raw.strip()
        if line.upper() in BLOCKS:
            if kind:
                yield kind, fields
            kind, fields = line.upper(), {}
        elif kind and ":" in line:
            label, value = line.split(":", 1)
            fields.setdefault(label.strip().lower(), value.strip())
    if kind:
        yield kind, fields


def _complete(kind: str, fields: dict, head_sha: str) -> bool:
    values = [fields.get(name, "") for name in BLOCKS[kind]]
    if any(not v or re.fullmatch(r"<.*>", v) for v in values):
        return False
    commit = fields["commit"].strip("`").lower()
    return len(commit) >= 7 and head_sha.lower().startswith(commit)


def evaluate(head_sha: str, comments: list) -> dict:
    valid = [(kind, fields, c["author"])
             for c in comments if not c["is_bot"] and c["permission"] in CAN_WRITE
             for kind, fields in _blocks(c["body"]) if _complete(kind, fields, head_sha)]
    emergency = next(({"author": a, "reason": f["motivo"]} for k, f, a in valid if k == "EMERGENZA"), None)
    if emergency:
        text = f"EMERGENZA dichiarata da {emergency['author']}: {emergency['reason']}"
    elif valid:
        text = f"Verifiche dichiarate da {valid[-1][2]}"
    else:
        text = f"Manca la risposta per il commit {head_sha[:7]}: vedi il commento nella PR"
    return {"state": "success" if valid else "failure", "description": text[:140], "emergency": emergency}
