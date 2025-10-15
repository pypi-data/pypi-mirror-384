def safe_signal(obj, signal_name: str, slot, warn_message: str = None):
    if hasattr(obj, signal_name):
        signal = getattr(obj, signal_name)
        signal.connect(slot)
    else:
        if warn_message is None:
            warn_message = f"Warning: {signal_name} does not exist on {obj}"
        print(warn_message)
