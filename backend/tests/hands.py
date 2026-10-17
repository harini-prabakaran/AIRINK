"""Synthetic hand landmarks for tests."""

W, H = 640, 480
# A synthetic hand pointing up, built in PIXEL space (hand scale = 100 px).
WRIST = (320, 400)
MCP = {"index": (285, 305), "middle": (320, 300), "ring": (355, 305), "pinky": (388, 315)}
IDX = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}


def build_hand(index=True, middle=True, ring=True, pinky=True, thumb=True, pinch=False):
    """Return 21 normalised (x, y, z) landmarks. True = extended, False = curled."""
    pts = [None] * 21
    pts[0] = WRIST
    for name, extended in (("index", index), ("middle", middle), ("ring", ring), ("pinky", pinky)):
        mx, my = MCP[name]
        i = IDX[name]
        pts[i] = (mx, my)
        if extended:
            pts[i + 1], pts[i + 2], pts[i + 3] = (mx, my - 45), (mx, my - 75), (mx, my - 100)
        else:  # curled: finger folds back over the palm
            pts[i + 1], pts[i + 2], pts[i + 3] = (mx, my - 40), (mx, my - 25), (mx, my - 5)
    if thumb:   # thumb sticks out to the left
        pts[1], pts[2], pts[3], pts[4] = (300, 385), (270, 360), (245, 335), (220, 310)
    else:       # thumb tucked across the palm
        pts[1], pts[2], pts[3], pts[4] = (305, 380), (315, 360), (325, 345), (335, 335)
    if pinch:
        pts[4] = pts[8]
    return [(x / W, y / H, 0.0) for x, y in pts]
