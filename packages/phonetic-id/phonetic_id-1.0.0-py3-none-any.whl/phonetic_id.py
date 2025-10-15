import secrets
from math import ceil

VOWELS: tuple[str, ...] = ('a', 'e', 'i', 'o', 'u')
"""Tuple of common vowels that are easy to pronounce in most languages."""

CONSONANTS: tuple[str, ...] = (
    'b', 'd', 'f', 'g', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'z'
)
"""Tuple of common consonants that are easy to pronounce in most languages."""


def construct_syllable() -> str:
    """Constructs a syllable using a random consonant and a random vowel, resulting in a 2-character string."""
    return secrets.choice(CONSONANTS) + secrets.choice(VOWELS)


def generate_phonetic_id(length: int, append_digits: int = 0) -> str:
    """Generates a phonetic ID with a total length of `length` characters (each syllable is 2 characters long).

    :param length: The total length of the phonetic ID (rounded up if needed).
    :type length: int
    :param append_digits: The number of digits to append at the end to increase entropy. Defaults to 0.
    :type append_digits: int, optional
    :return: A randomly generated phonetic ID.
    :rtype: str
    """
    phonetic_id: str = ""

    for _ in range(ceil(length / 2)):
        phonetic_id += construct_syllable()

    if append_digits > 0:
        system_random: secrets.SystemRandom = secrets.SystemRandom()

        for _ in range(append_digits):
            phonetic_id += str(system_random.randint(0, 9))

    return phonetic_id


if __name__ == "__main__":
    print(generate_phonetic_id(length=8))
    print(generate_phonetic_id(length=8, append_digits=2))
