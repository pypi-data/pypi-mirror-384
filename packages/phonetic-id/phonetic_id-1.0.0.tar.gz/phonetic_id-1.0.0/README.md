Phonetic ID is a lightweight package for generating a easy to say ID

# Usage

```python
from phonetic_id import generate_phonetic_id

generate_phonetic_id(length=8) # mebifeka
generate_phonetic_id(length=8, append_digits=2) # motizigo58
```

# Entropy

Phonetic IDs have low entropy, so they should not be used for cryptographic purposes.

## Info

The length is always rounded to an even number.  
There are 5 vowels and 14 consonants.  
Each syllable consists of 1 vowel and 1 consonant, allowing for:

5 \* 14 = 70 unique syllables

For example, `generate_phonetic_id(length=8)` produces 4 syllables (since each syllable has 2 characters), resulting in:

70^4 = 24,010,000 combinations
~24.51 bits of entropy

## Entropy Table

| Length |    Combinations     | Entropy (bits) |
| :----: | :-----------------: | :------------: |
|   2    |         70          |     ~6.13      |
|   4    |        4,900        |     ~12.26     |
|   6    |       343,000       |     ~18.39     |
|   8    |     24,010,000      |     ~24.52     |
|   10   |    1,680,700,000    |     ~30.65     |
|   12   |   117,649,000,000   |     ~36.78     |
|   14   |  8,235,430,000,000  |     ~42.90     |
|   16   | 576,480,100,000,000 |     ~49.03     |

## Increasing Entropy

You can increase entropy by using the `append_digits` argument, which adds N digits to the end.  
This effectively multiplies the total number of combinations by 10^N.
