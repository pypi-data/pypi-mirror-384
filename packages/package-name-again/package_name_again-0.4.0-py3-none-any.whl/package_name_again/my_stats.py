from scipy.stats import binom


def design_stats_test(fair_probability, unfair_probability, confidence=0.95):
    num_measurements = 2
    roll_test = binom.ppf(confidence, num_measurements, fair_probability) - binom.ppf(1 - confidence, num_measurements, unfair_probability
    )

    while roll_test > 0:
        num_measurements += 1
        roll_test = binom.ppf(confidence, num_measurements, fair_probability) - binom.ppf(1 - confidence, num_measurements, unfair_probability)
    return num_measurements, binom.ppf(confidence, num_measurements, fair_probability)


def design_stats_test_UI():
    fair_prob = float(input("Fair Probability: "))
    unfair_prob = float(input("Unfair Probability: "))
    confidence_int = float(input("Confidence Interval: "))
    num_measurements, boundary = design_stats_test(fair_prob, unfair_prob, confidence_int)
    print(num_measurements,"measurements needed.","Greater than",boundary,"is a cheater")


if __name__ == "__main__":
    print(design_stats_test(0.5, 0.75))