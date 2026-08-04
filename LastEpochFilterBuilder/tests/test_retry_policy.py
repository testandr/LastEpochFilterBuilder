from app.utils.retry import RetryPolicy


def test_retry_delays():
    rp = RetryPolicy(attempts=4, delay_seconds=1.0, backoff_factor=2.0)
    # attempt 1 -> 0.0
    assert rp.get_delay(1) == 0.0
    # attempt 2 -> 1.0 * 2^(1) = 2.0
    assert rp.get_delay(2) == 1.0 * (2.0 ** 1)
    # attempt 3 -> 1.0 * 2^(2) = 4.0
    assert rp.get_delay(3) == 1.0 * (2.0 ** 2)
    # attempt 4 -> 8.0
    assert rp.get_delay(4) == 1.0 * (2.0 ** 3)
