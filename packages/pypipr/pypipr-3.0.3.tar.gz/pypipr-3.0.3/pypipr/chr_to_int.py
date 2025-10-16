def chr_to_int(s, start=0, numbers="abcdefghijklmnopqrstuvwxyz"):
    """
    Fungsi ini berguna untuk mengubah urutan huruf menjadi angka.
    dimulai dari a = 0
    """
    result = 0
    digit = len(numbers)
    for char in s:
        result = result * digit + numbers.index(char) + 1
    return result + start - 1


def test():
    print(chr_to_int("a"))
    print(chr_to_int("z"))
    print(chr_to_int("ac"))
    print(chr_to_int("abc", numbers="abcde"))
