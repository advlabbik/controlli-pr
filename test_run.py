import unittest

from compat import run


class FakeApi:
    """GitHub finto: tiene commenti, etichette e stati come farebbe quello vero."""

    def __init__(self, head="abc1234def5678", comments=(), permissions=None, state="open"):
        self.head, self.state = head, state
        self.comments = list(comments)
        self.permissions = permissions or {"anna": "write"}
        self.labels, self.statuses = [], []

    def __call__(self, method, path, body=None):
        if method == "GET" and path.endswith("/pulls/7"):
            return {"state": self.state, "head": {"sha": self.head}}
        if method == "GET" and "/issues/7/comments" in path:
            page = int(path.rsplit("page=", 1)[1])
            return self.comments[(page - 1) * 100:page * 100]
        if method == "GET" and "/collaborators/" in path:
            return {"permission": self.permissions.get(path.split("/")[-2], "read")}
        if method == "POST" and path.endswith("/issues/7/comments"):
            self.comments.append({"body": body["body"], "user": {"login": "github-actions[bot]", "type": "Bot"}})
        elif method == "POST" and path.endswith("/issues/7/labels"):
            self.labels += body["labels"]
        elif method == "POST" and "/statuses/" in path:
            self.statuses.append((path.rsplit("/", 1)[1], body))
        else:
            raise AssertionError(f"chiamata inattesa {method} {path}")


def human(body, login="anna"):
    return {"body": body, "user": {"login": login, "type": "User"}}


def bot_bodies(api, marker):
    return [c["body"] for c in api.comments if c["user"]["type"] == "Bot" and marker in c["body"]]


SOS = "EMERGENZA\nCommit: abc1234\nMotivo: sito giù, chiedi a @qualcuno"


class Esecuzione(unittest.TestCase):
    def test_richiesta_pubblicata_una_volta_e_stato_rosso(self):
        api = FakeApi()
        run("advlabbik/x", 7, api)
        run("advlabbik/x", 7, api)
        self.assertEqual(len(bot_bodies(api, "<!-- compatibilita-main -->")), 1)
        sha, status = api.statuses[-1]
        self.assertEqual((sha, status["state"], status["context"]), ("abc1234def5678", "failure", "compatibilita-main"))

    def test_il_modello_della_richiesta_non_vale_nemmeno_ricopiato(self):
        api = FakeApi()
        run("advlabbik/x", 7, api)
        api.comments.append(human(bot_bodies(api, "<!-- compatibilita-main -->")[0]))
        run("advlabbik/x", 7, api)
        self.assertEqual(api.statuses[-1][1]["state"], "failure")

    def test_un_umano_che_cita_il_marcatore_non_blocca_la_richiesta(self):
        api = FakeApi(comments=[human("<!-- compatibilita-main -->")])
        run("advlabbik/x", 7, api)
        self.assertEqual(len(bot_bodies(api, "<!-- compatibilita-main -->")), 1)

    def test_stato_sull_ultimo_commit_e_commenti_oltre_la_prima_pagina(self):
        reply = "COMPATIBILITA-MAIN\nCommit: fff0000\nAggiornato con main: sì\nTest eseguiti: ok\nNon verificato: niente"
        api = FakeApi(head="fff0000aaa", comments=[human("x")] * 100 + [human(reply)])
        run("advlabbik/x", 7, api)
        self.assertEqual((api.statuses[-1][0], api.statuses[-1][1]["state"]), ("fff0000aaa", "success"))

    def test_permesso_letto_da_github(self):
        api = FakeApi(comments=[human(SOS, login="estraneo")])
        run("advlabbik/x", 7, api)
        self.assertEqual(api.statuses[-1][1]["state"], "failure")
        self.assertEqual(api.labels, [])

    def test_emergenza_etichetta_e_un_solo_avviso(self):
        api = FakeApi(comments=[human(SOS)])
        run("advlabbik/x", 7, api)
        run("advlabbik/x", 7, api)
        notices = bot_bodies(api, "<!-- emergenza:abc1234 -->")
        self.assertEqual(len(notices), 1)
        self.assertIn("@vietts", notices[0])
        self.assertIn("`sito giù, chiedi a @qualcuno`", notices[0])  # nessuna menzione dal motivo
        self.assertIn("emergenza", api.labels)
        self.assertEqual(api.statuses[-1][1]["state"], "success")

    def test_commento_cancellato_torna_rosso(self):
        api = FakeApi(comments=[human(SOS)])
        run("advlabbik/x", 7, api)
        api.comments = [c for c in api.comments if c["user"]["type"] == "Bot"]
        run("advlabbik/x", 7, api)
        self.assertEqual(api.statuses[-1][1]["state"], "failure")

    def test_pr_chiusa_nessuna_scrittura(self):
        api = FakeApi(state="closed")
        run("advlabbik/x", 7, api)
        self.assertEqual((api.statuses, api.comments), ([], []))


if __name__ == "__main__":
    unittest.main()
