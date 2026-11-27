# controlli-pr

Controllo `compatibilita-main` sulle pull request: chiede cosa è stato verificato rispetto a `main`
e resta rosso finché non c'è una risposta (o un'emergenza motivata). Non giudica il contenuto.

Per usarlo in un repo si copia `caller.yml` in `.github/workflows/compatibilita.yml`.
Il testo della richiesta è in `richiesta.md`. Test: `python3 -m unittest -v`.

Questo repo è pubblico: niente segreti né dati interni.
