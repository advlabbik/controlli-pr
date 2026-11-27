import unittest

from compat import evaluate

SHA = "abc1234def5678"


def c(body, permission="write", is_bot=False, author="anna"):
    return {"body": body, "author": author, "permission": permission, "is_bot": is_bot}


def reply(commit="abc1234", tests="npm test: passati"):
    return (f"COMPATIBILITA-MAIN\nCommit: {commit}\nAggiornato con main: sì, nessun conflitto\n"
            f"Test eseguiti: {tests}\nNon verificato: niente")


SOS = "EMERGENZA\nCommit: abc1234\nMotivo: checkout fermo in produzione"


def state(*comments):
    return evaluate(SHA, list(comments))["state"]


class Risposta(unittest.TestCase):
    def test_senza_commenti_rosso(self):
        self.assertEqual(state(), "failure")

    def test_risposta_completa_verde(self):
        self.assertEqual(state(c(reply())), "success")

    def test_tre_apici_spazi_e_maiuscole(self):
        body = "Ecco:\n```\n  " + reply().replace("Commit:", "commit :").replace("COMPATIBILITA", "Compatibilita") + "\n```"
        self.assertEqual(state(c(body)), "success")

    def test_commit_vecchio_o_corto(self):
        self.assertEqual(state(c(reply(commit="999999a"))), "failure")
        self.assertEqual(state(c(reply(commit="abc"))), "failure")

    def test_campo_vuoto_o_modello_non_compilato(self):
        self.assertEqual(state(c(reply(tests=""))), "failure")
        self.assertEqual(state(c(reply(tests="<comandi o build>"))), "failure")

    def test_serve_accesso_in_scrittura(self):
        self.assertEqual(state(c(reply(), permission="read")), "failure")
        self.assertEqual(state(c(reply(), is_bot=True)), "failure")
        self.assertEqual(state(c(reply(), permission="admin")), "success")

    def test_blocco_valido_dopo_uno_vecchio(self):
        self.assertEqual(state(c(reply(commit="999999a") + "\n\n" + reply())), "success")


class Markdown(unittest.TestCase):
    def test_formattazioni_comuni_valgono(self):
        for old, new in [
            ("COMPATIBILITA-MAIN", "**COMPATIBILITA-MAIN**"), ("COMPATIBILITA-MAIN", "### COMPATIBILITA-MAIN"),
            ("COMPATIBILITA-MAIN", "COMPATIBILITA MAIN"), ("COMPATIBILITA-MAIN", "COMPATIBILITÀ-MAIN"),
            ("COMPATIBILITA-MAIN", "COMPATIBILITA-MAIN:"), ("Commit:", "**Commit:**"), ("Commit:", "- Commit:"),
            ("Aggiornato con main:", "Aggiornato  con main:"), ("Aggiornato con main:", "Aggiornato\u00a0con main:"),
            ("Commit: abc1234", "Commit: abc1234 (ultimo)"), ("Test eseguiti:", "* __Test eseguiti__:"),
        ]:
            with self.subTest(new=new):
                self.assertEqual(state(c(reply().replace(old, new))), "success")

    def test_la_formattazione_non_rende_valido_cio_che_non_lo_e(self):
        self.assertEqual(state(c(reply(tests="**<comandi o build>**"))), "failure")
        self.assertEqual(state(c(reply(tests="**"))), "failure")
        self.assertEqual(state(c(reply().replace("COMPATIBILITA-MAIN", "la compatibilità main è ok"))), "failure")
        self.assertEqual(state(c("Emergenza?\nCommit: abc1234\nMotivo: x")), "failure")
        self.assertEqual(state(c(SOS.replace("EMERGENZA", "**EMERGENZA**"))), "success")


class Emergenza(unittest.TestCase):
    def test_emergenza_motivata(self):
        r = evaluate(SHA, [c(SOS)])
        self.assertEqual(r["state"], "success")
        self.assertEqual(r["emergency"], {"author": "anna", "reason": "checkout fermo in produzione"})

    def test_emergenza_incompleta_o_vecchia(self):
        self.assertEqual(state(c("EMERGENZA\nCommit: abc1234\nMotivo:")), "failure")
        self.assertEqual(state(c("EMERGENZA\nMotivo: urgente")), "failure")
        self.assertEqual(state(c(SOS.replace("abc1234", "999999a"))), "failure")
        self.assertEqual(state(c(SOS, permission="read")), "failure")

    def test_parola_in_una_frase_non_basta(self):
        self.assertEqual(state(c("non è un'emergenza\nCommit: abc1234\nMotivo: x")), "failure")

    def test_risposta_normale_non_e_emergenza(self):
        self.assertIsNone(evaluate(SHA, [c(reply())])["emergency"])

    def test_descrizione_corta(self):
        for comments in ([], [c(reply())], [c(SOS + "x" * 300)]):
            self.assertLessEqual(len(evaluate(SHA, comments)["description"]), 140)


if __name__ == "__main__":
    unittest.main()
