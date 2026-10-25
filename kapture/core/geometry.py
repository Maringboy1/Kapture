def even(n):
    n = int(n)
    if n < 2:
        return 2 if n > 0 else 0
    return n - (n % 2)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rect_tuple(x, y, w, h):
    return (int(x), int(y), max(1, int(w)), max(1, int(h)))


def center_of(rect):
    x, y, w, h = rect
    return (x + w // 2, y + h // 2)


def contains(rect, px, py):
    x, y, w, h = rect
    return x <= px < x + w and y <= py < y + h


def union_rects(rects):
    if not rects:
        return None
    xs = [r[0] for r in rects]
    ys = [r[1] for r in rects]
    xe = [r[0] + r[2] for r in rects]
    ye = [r[1] + r[3] for r in rects]
    return (min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys))
