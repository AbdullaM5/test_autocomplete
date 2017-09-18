import random
import string


def get_random_string():
    return ''.join([
        random.choice(string.ascii_lowercase)
        for _ in range(random.randint(1, 15))
    ])


if __name__ == '__main__':
    with open('word_freq.txt', 'w') as f:
        for i in range(0, 100000):
            rnd_str = get_random_string()
            rnd_int = str(random.randint(1, 10 ** 6))
            f.write(' '.join([rnd_str, rnd_int, '\n']))

