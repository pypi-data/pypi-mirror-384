from enum import Enum


class SearchAlgorithm(Enum):
    beam_search = "beam_search"
    dssd = "dssd"

    def __str__(self):
        return self.value
