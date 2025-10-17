from iterwrap import IterateWrapper, iterate_wrapper


def _perform_operation(f_io, item: int, add_args: dict):
    from time import sleep

    global _tmp
    if item == 0:
        if _tmp:
            _tmp = False
            raise ValueError("here")
    result = item * item
    f_io.write(str(result) + "\n")
    return result


def _test_fn():
    data = list(range(10))
    num_workers = 3
    returns = iterate_wrapper(_perform_operation, data, "tmp.txt", add_args={"a": 1}, num_workers=num_workers)
    print(returns)


def _test_wrapper():
    from time import sleep

    for i in IterateWrapper(range(10)):
        sleep(1)


if __name__ == "__main__":
    _tmp = True
    _test_fn()
