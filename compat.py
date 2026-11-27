"""Stato «compatibilita-main» di una PR, ricavato dai suoi commenti."""
import json
import os
import pathlib
import re
import subprocess

CONTEXT = "compatibilita-main"
REQUEST_MARKER = "<!-- compatibilita-main -->"

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


def _all_comments(repo: str, number: int, api) -> list:
    out, page = [], 1
    while True:
        batch = api("GET", f"repos/{repo}/issues/{number}/comments?per_page=100&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def run(repo: str, number: int, api) -> None:
    pr = api("GET", f"repos/{repo}/pulls/{number}")
    if pr["state"] != "open":
        return
    head = pr["head"]["sha"]  # quello attuale, non quello dell'evento
    raw = _all_comments(repo, number, api)
    permissions, comments, published = {}, [], []
    for item in raw:
        user, body = item["user"], item["body"] or ""
        if user["type"] == "Bot":
            published.append(body)
            continue
        login = user["login"]
        # il permesso vero: author_association sbaglia con le appartenenze private
        if login not in permissions and any(True for _ in _blocks(body)):
            permissions[login] = api("GET", f"repos/{repo}/collaborators/{login}/permission")["permission"]
        comments.append({"body": body, "author": login, "permission": permissions.get(login, "none"), "is_bot": False})

    def comment(text):
        api("POST", f"repos/{repo}/issues/{number}/comments", {"body": text})

    if not any(REQUEST_MARKER in body for body in published):
        comment((pathlib.Path(__file__).parent / "richiesta.md").read_text())

    result = evaluate(head, comments)
    if result["emergency"]:
        marker = f"<!-- emergenza:{head[:7]} -->"
        if not any(marker in body for body in published):
            api("POST", f"repos/{repo}/issues/{number}/labels", {"labels": ["emergenza"]})
            reason = result["emergency"]["reason"].replace("`", "'")
            comment(f"{marker}\n**Emergenza** sul commit `{head[:7]}`, dichiarata da `{result['emergency']['author']}`. "
                    f"Motivo: `{reason}`\n\nAvviso per @vietts. Dopo il merge fate le verifiche rispetto a `main` "
                    "e scrivete qui il risultato.")
    api("POST", f"repos/{repo}/statuses/{head}",
        {"state": result["state"], "context": CONTEXT, "description": result["description"]})


def gh_api(method: str, path: str, body=None):
    cmd = ["gh", "api", "--method", method, path] + (["--input", "-"] if body is not None else [])
    r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None,
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"Errore API su {method} {path}: {r.stdout} {r.stderr}")
    return json.loads(r.stdout) if r.stdout.strip() else None


def main() -> None:
    run(os.environ["GITHUB_REPOSITORY"], int(os.environ["PR_NUMBER"]), gh_api)


if __name__ == "__main__":
    main()
