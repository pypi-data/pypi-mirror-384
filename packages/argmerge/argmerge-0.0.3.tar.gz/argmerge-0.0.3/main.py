from argmerge import threshold


@threshold(trace_level="DEBUG")
def main(first, second, third: float = 3.0, fourth: float = 4.0, fifth: int = 5):
    pass


if __name__ == "__main__":
    main(first=1, second="second")
