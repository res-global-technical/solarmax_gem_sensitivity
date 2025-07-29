def format_time_taken(elapsed_time_secs: float) -> str:
    if elapsed_time_secs < 1:
        return f"{elapsed_time_secs * 1000:.0f} ms"
    if elapsed_time_secs < 60:
        return f"{elapsed_time_secs:.2f} secs"
    if elapsed_time_secs < 3600:
        return f"{elapsed_time_secs / 60:.2f} mins"
    return f"{elapsed_time_secs / 3600:.2f} hours"
