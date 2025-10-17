class PaginationInfo:
    page: int = 1
    size: int = 10

    def __init__(self, page, size):
        self.page = page
        self.size = size
