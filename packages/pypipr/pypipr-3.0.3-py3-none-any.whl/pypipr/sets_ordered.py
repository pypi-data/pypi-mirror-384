def sets_ordered(iterator):
    """
    Hanya mengambil nilai unik dari suatu list

    ```python
    array = [2, 3, 12, 3, 3, 42, 42, 1, 43, 2, 42, 41, 4, 24, 32, 42, 3, 12, 32, 42, 42]
    print(sets_ordered(array))
    print(list(sets_ordered(array)))
    ```
    """
    for i in dict.fromkeys(iterator):
        yield i
