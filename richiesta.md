<!-- compatibilita-main -->
### Claude: cosa hai verificato rispetto a `main`?

Il controllo **`compatibilita-main`** resta rosso finché non rispondi con un commento in questo formato, compilando tutti i campi.

**Verifica prima di rispondere.** Porta il ramo a confronto con l'ultimo `main`, guarda i conflitti, esegui i test o la build. Non dichiarare test che non hai eseguito: se non ce ne sono o non puoi lanciarli, scrivilo.

```
COMPATIBILITA-MAIN
Commit: <primi 7 caratteri dell'ultimo commit della PR>
Aggiornato con main: <sì o no, ed eventuali conflitti>
Test eseguiti: <comandi o build, con il risultato; se nessuno, perché>
Non verificato: <cosa resta scoperto, oppure «niente»>
```

Con un nuovo commit serve una nuova risposta.

<details><summary>Emergenza: la PR va unita subito</summary>

Solo se non si può aspettare, e solo se te lo chiede la persona per cui lavori:

```
EMERGENZA
Commit: <primi 7 caratteri dell'ultimo commit della PR>
Motivo: <perché non si può aspettare>
```

Il controllo diventa verde, la PR viene etichettata e parte un avviso. Le verifiche vanno fatte dopo il merge.
**L'emergenza non salta i test automatici obbligatori.**
</details>
