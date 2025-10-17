class MISSING_TYPE:
    def __bool__(self) -> bool:
        return False

    pass


MISSING = MISSING_TYPE()
