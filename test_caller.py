import pathlib
import re
import unittest

CALLER = (pathlib.Path(__file__).parent / "caller.yml").read_text()


class Caller(unittest.TestCase):
    def test_i_commenti_irrilevanti_non_fanno_partire_il_job(self):
        for word in ("COMPATIBILITA", "EMERGENZA"):
            # commento nuovo o cancellato, e commento da cui la parola è stata tolta modificandolo
            self.assertIn(f"contains(github.event.comment.body, '{word}')", CALLER)
            self.assertIn(f"contains(github.event.changes.body.from, '{word}')", CALLER)

    def test_la_coda_e_sul_job_non_sul_workflow(self):
        # sul workflow, un'esecuzione da saltare potrebbe annullarne una utile in attesa
        self.assertIsNone(re.search(r"^concurrency:", CALLER, re.M))
        self.assertIsNotNone(re.search(r"^    concurrency:", CALLER, re.M))


if __name__ == "__main__":
    unittest.main()
