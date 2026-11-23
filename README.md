# Soundarya Lahari reader

A study site for the Soundarya Lahari (attributed to Adi Shankaracharya), built for family learning.
Verses 1 to 5 so far, in Devanagari, Telugu and IAST, with meanings, word-by-word glosses,
a syllable-by-syllable meter view (Shikharini), a word and root index, a concept map,
memorisation tools and short guided paths.

Live site: https://hariongithub.github.io/soundarya-lahari/

## How it works
- Everything is one file, `index.html`. The verse data is the `DATA` object near the end of the file; `SCAN` holds the meter analysis.
- `tools/gen_scan.py` reads `DATA` from `index.html` and regenerates the meter data (`scan.json`).
- Telugu is copied exactly from a printed Telugu edition. Devanagari and IAST are converted from it by script.
- Meanings, glosses, root notes, the concept map and guided paths are drafts and have not been reviewed by a teacher.

## Audio
Not added yet.
