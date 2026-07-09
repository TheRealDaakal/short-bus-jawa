def ease_out_quart(t: float) -> float:
    """Starts fast, decelerates smoothly to a stop at t=1."""
    return 1 - (1 - t) ** 4
