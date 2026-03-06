def classify_signal_vs_noise(efficiency_shift: float, quality_shift: float, volume_shift: float, pressure_context: float, variance_flag: bool, sample_size: int):
    if sample_size < 3:
        return ("variance", "small sample")
    if variance_flag and abs(quality_shift) < 0.2:
        return ("variance", "outcome noise > process")
    signals = 0
    if abs(efficiency_shift) >= 0.3: signals += 1
    if abs(quality_shift) >= 0.3: signals += 1
    if abs(volume_shift) >= 0.3: signals += 1
    if pressure_context >= 0.7: signals += 1
    if signals >= 3:
        return ("signal", "multiple process indicators shifted")
    if signals == 2:
        return ("lean", "possible signal, needs reps")
    return ("variance", "scoreboard moved more than process")
