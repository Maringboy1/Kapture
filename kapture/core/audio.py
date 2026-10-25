import subprocess


def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)


def default_sink():
    rc, out, _ = run(["pactl", "get-default-sink"])
    return out.strip() if rc == 0 else None


def default_source():
    rc, out, _ = run(["pactl", "get-default-source"])
    return out.strip() if rc == 0 else None


def list_sources():
    rc, out, _ = run(["pactl", "list", "short", "sources"])
    res = []
    if rc != 0:
        return res
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            res.append({"id": parts[0], "name": parts[1], "desc": " ".join(parts[4:]) if len(parts) > 4 else ""})
    return res


def monitor_sources():
    return [s for s in list_sources() if s["name"].endswith(".monitor")]


def mic_sources():
    return [s for s in list_sources() if not s["name"].endswith(".monitor")]


def desktop_source():
    sink = default_sink()
    if sink:
        mon = sink + ".monitor"
        if any(s["name"] == mon for s in list_sources()):
            return mon
    mons = monitor_sources()
    return mons[0]["name"] if mons else None


def mic_source():
    src = default_source()
    if src and not src.endswith(".monitor"):
        return src
    mics = mic_sources()
    return mics[0]["name"] if mics else None


def audio_available():
    return len(list_sources()) > 0
