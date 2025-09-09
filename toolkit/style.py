def stylize(text, channel="ui", session_id=None, corr_id=None):
    sid = session_id or "-"
    cid = corr_id or "-"
    return f"[NEON][{channel}][sid:{sid}][cid:{cid}] {text}"
