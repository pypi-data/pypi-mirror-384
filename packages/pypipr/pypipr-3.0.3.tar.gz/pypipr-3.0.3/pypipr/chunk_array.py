import pprint


def chunk_array(array, size, start=0):
    """
    Membagi array menjadi potongan-potongan dengan besaran yg diinginkan
    """
    for i in range(start, len(array), size):
        yield array[i : i + size]

def test():
    arr = [2, 3, 12, 3, 3, 42, 42, 1, 43, 2, 42, 41, 4, 24, 32, 42, 3, 12, 32, 42, 42]
    print(chunk_array(arr, 5))
    pprint.pprint(list(chunk_array(arr, 5)))
