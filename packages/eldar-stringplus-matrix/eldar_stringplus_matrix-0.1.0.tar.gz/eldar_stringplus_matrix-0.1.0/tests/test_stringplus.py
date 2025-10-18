from stringplus import reverse, count_vowels, is_palindrome, replace_numbers, only_letters

assert reverse('hello') == 'olleh'
assert count_vowels('hello') == 2
assert is_palindrome('level') == True
assert is_palindrome('hello') == False
assert replace_numbers('I have 2 apples') == 'I have two apples'
assert only_letters('Hello123!') == 'Hello'

print('? All tests passed!')
