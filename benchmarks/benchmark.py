import timeit
import lstring

def benchmark():
    # Prepare long strings
    py_str = "abcdefghijklmnopqrstuvwxyz" * 100000
    lstr_obj = lstring.L(py_str)

    # Define operations
    def py_slice_concat():
        s1 = py_str[1000:50000]
        s2 = py_str[7000:12000]
        return s1 + s2

    def lstr_slice_concat():
        s1 = lstr_obj[1000:50000]
        s2 = lstr_obj[7000:12000]
        return s1 + s2

    def py_repeat_slice():
        return (py_str[1000:50000] * 3)[100:50000]

    def lstr_repeat_slice():
        return (lstr_obj[1000:50000] * 3)[100:50000]

    # Run benchmarks
    n = 100000
    py_time1 = timeit.timeit(py_slice_concat, number=n)
    lstr_time1 = timeit.timeit(lstr_slice_concat, number=n)

    py_time2 = timeit.timeit(py_repeat_slice, number=n)
    lstr_time2 = timeit.timeit(lstr_repeat_slice, number=n)

    print("Slice + concat:")
    print(f"  Python str: {py_time1:.4f} sec")
    print(f"  L:          {lstr_time1:.4f} sec")
    print("Repeat + slice:")
    print(f"  Python str: {py_time2:.4f} sec")
    print(f"  L:          {lstr_time2:.4f} sec")

if __name__ == "__main__":
    benchmark()
