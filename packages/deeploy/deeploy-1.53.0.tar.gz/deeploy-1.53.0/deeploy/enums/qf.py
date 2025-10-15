from enum import Enum


class QualityFactor(Enum):
    demographic_parity_difference = "demographic_parity_difference"
    demographic_parity_ratio = "demographic_parity_ratio"
    equalized_odds_difference = "equalized_odds_difference"
    equalized_odds_ratio = "equalized_odds_ratio"

    def __str__(self):
        return self.value
