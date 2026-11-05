# Resentence

Sentence flashcards built from the words saved in Rewords.
Each card shows the English sentence with the saved word(s) highlighted; tap to reveal meanings.

**Live:** https://chenjing002.github.io/Resentence/

Keys: `←` `→` navigate · `Space` reveal · `S` shuffle · `L` listen. Swipe on touch screens.

## How it updates

- `build.py` reads `rewords-vocabulary.json` (iCloud Drive › Rewords), keeps only the English part of each
  saved sentence, merges duplicate / truncated copies of the same sentence, and writes `sentences.json`.
- `sync.sh` runs `build.py`, commits `sentences.json` if it changed, and pushes when GitHub is reachable.
- `install.sh` installs a launchd agent (`com.chenjing002.resentence`) that runs `sync.sh` whenever the
  export file changes, when the network changes, and every 15 minutes, so commits made offline are pushed
  once the network is back. Log: `sync.log`.
