def reverse(text: str) -> str:
    return text[::-1]

def count_vowels(text: str) -> int:
    return sum(1 for c in text.lower() if c in 'aeiou')

def is_palindrome(text: str) -> bool:
    clean = ''.join(c.lower() for c in text if c.isalnum())
    return clean == clean[::-1]

def replace_numbers(text: str) -> str:
    num_dict = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }
    return ''.join(num_dict.get(c, c) for c in text)

def only_letters(text: str) -> str:
    return ''.join(c for c in text if c.isalpha())
