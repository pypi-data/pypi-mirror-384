# Sanskritizer

Convert English words to Sanskrit transliterations: IAST, Devanagari, and pronunciation.

## Installation
```bash
pip install sanskritizer

### Usage
from sanskritizer import to_iaST, to_devanagari, pronunciation

print(to_iaST("peace"))         # śānti
print(to_devanagari("peace"))   # शान्ति
print(pronunciation("peace"))   # shaanti