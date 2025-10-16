import random

import pyqtree
import pytest

# Import your shim
from fastquadtree.pyqtree import Index as FQTIndex

WORLD = (0.0, 0.0, 100.0, 100.0)


def rand_rect(rng, world=WORLD, min_size=1.0, max_size=20.0):
    x1 = rng.uniform(world[0], world[2] - min_size)
    y1 = rng.uniform(world[1], world[3] - min_size)
    w = rng.uniform(min_size, max_size)
    h = rng.uniform(min_size, max_size)
    x2 = min(world[2], x1 + w)
    y2 = min(world[3], y1 + h)
    return (x1, y1, x2, y2)


def build_indices(items, ctor="bbox"):
    """
    items: list[tuple[item_obj, (xmin, ymin, xmax, ymax)]]
    ctor: "bbox" or "xywh"
    """
    if ctor == "bbox":
        fqt = FQTIndex(bbox=WORLD)
        pyq = pyqtree.Index(bbox=WORLD)
    elif ctor == "xywh":
        x = (WORLD[0] + WORLD[2]) / 2.0
        y = (WORLD[1] + WORLD[3]) / 2.0
        w = WORLD[2] - WORLD[0]
        h = WORLD[3] - WORLD[1]
        fqt = FQTIndex(x=x, y=y, width=w, height=h)
        pyq = pyqtree.Index(x=x, y=y, width=w, height=h)
    else:
        raise ValueError("bad ctor")

    for obj, box in items:
        # Both APIs are item, bbox
        ret1 = fqt.insert(obj, box)
        ret2 = pyq.insert(obj, box)
        # pyqtree returns None, so enforce parity
        assert ret1 is None
        assert ret2 is None

    return fqt, pyq


def results_match_exact(fqt, pyq, query):
    """Compare lists exactly, not just as sets."""
    got_fqt = sorted(fqt.intersect(query))
    got_pyq = sorted(pyq.intersect(query))
    assert (
        got_fqt == got_pyq
    ), f"\nquery={query}\nfastquadtree={got_fqt}\npyqtree={got_pyq}"


def test_ctor_error_branch():
    # Exercise the constructor error path for 100% coverage
    with pytest.raises(ValueError):
        FQTIndex()  # neither bbox nor x,y,width,height


@pytest.mark.parametrize("ctor", ["bbox", "xywh"])
def test_basic_insert_intersect_remove_matches_pyqtree(ctor):
    rng = random.Random(123)
    # Make a small deterministic dataset with some overlaps and some isolated
    items = [(name, rand_rect(rng)) for name in ["a", "b", "c", "d", "e", "f", "g"]]

    fqt, pyq = build_indices(items, ctor=ctor)

    # Queries that hit various cases
    queries = [
        (0, 0, 1, 1),  # miss everything
        (10, 10, 90, 90),  # broad overlap
        items[0][1],  # exactly the first item's bbox
        items[-1][1],  # exactly the last item's bbox
        (25, 25, 26, 26),  # tiny box
        (0, 0, 100, 100),  # world box
    ]

    for q in queries:
        results_match_exact(fqt, pyq, q)

    # Remove two items and recheck
    to_remove = [items[1], items[4]]  # remove b and e
    for obj, box in to_remove:
        fqt.remove(obj, box)
        pyq.remove(obj, box)

    # After removal, both should match on the same queries
    for q in queries:
        results_match_exact(fqt, pyq, q)

    # Also check that removed objects are truly gone
    for obj, box in to_remove:
        assert obj not in fqt.intersect(box)
        assert obj not in pyq.intersect(box)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_randomized_equivalence_many_queries(seed):
    rng = random.Random(seed)
    # More items to stress traversal order
    items = [(f"obj_{i}", rand_rect(rng)) for i in range(50)]
    fqt, pyq = build_indices(items, ctor="bbox")

    # 30 random queries
    queries = [rand_rect(rng, max_size=40.0) for _ in range(30)]
    for q in queries:
        results_match_exact(fqt, pyq, q)


def test_order_is_identical_to_pyqtree_for_same_insert_order():
    """
    pyqtree does not document result ordering, but many users
    implicitly depend on the current behavior. This test locks
    your shim to whatever pyqtree returns.
    """
    # Crafted rectangles that overlap in a chainy way
    items = [
        ("one", (10, 10, 30, 30)),
        ("two", (20, 20, 40, 40)),
        ("three", (15, 15, 35, 35)),
        ("four", (12, 12, 18, 18)),
        ("five", (28, 28, 45, 45)),
    ]
    fqt, pyq = build_indices(items, ctor="bbox")
    q = (14, 14, 29, 29)
    # Compare lists directly for strict equality
    assert fqt.intersect(q) == pyq.intersect(q)


def test_insert_and_remove_return_none_and_accepts_any_object():
    # Mixed object types as items
    items = [
        ({"id": 1}, (5, 5, 10, 10)),
        (("tuple", 2), (8, 8, 12, 12)),
        (42, (0, 0, 3, 3)),
        ("str", (1, 1, 2, 2)),
    ]
    fqt, pyq = build_indices(items, ctor="bbox")

    # Both insert already asserted to return None inside build_indices
    # Now remove and assert None as well
    for obj, box in items:
        assert fqt.remove(obj, box) is None
        assert pyq.remove(obj, box) is None

    # All gone now
    assert fqt.intersect((0, 0, 100, 100)) == []
    assert pyq.intersect((0, 0, 100, 100)) == []


def _rect(x1, y1, x2, y2):
    return (x1, y1, x2, y2)


def test_free_slot_reuse_single_and_lifo():
    idx = FQTIndex(bbox=WORLD)

    # Insert three distinct items at non-overlapping places
    a, b, c = "a", "b", "c"
    ra = _rect(0, 0, 10, 10)
    rb = _rect(20, 20, 30, 30)
    rc = _rect(40, 40, 50, 50)

    assert idx.insert(a, ra) is None
    assert idx.insert(b, rb) is None
    assert idx.insert(c, rc) is None

    # RIDs are dense: 0, 1, 2
    rid_a = idx._item_to_id[id(a)]
    rid_b = idx._item_to_id[id(b)]
    rid_c = idx._item_to_id[id(c)]
    assert (rid_a, rid_b, rid_c) == (0, 1, 2)

    # Remove c then a to create two free slots; free should be [2, 0]
    assert idx.remove(c, rc) is None
    assert idx.remove(a, ra) is None
    assert idx._objects[rid_c] is None
    assert idx._objects[rid_a] is None
    assert idx._free == [rid_c, rid_a]

    before_len = len(idx._objects)

    # Insert x. It should reuse last freed slot (LIFO): rid_a
    x, rx = "x", _rect(60, 60, 70, 70)
    assert idx.insert(x, rx) is None
    rid_x = idx._item_to_id[id(x)]
    assert rid_x == rid_a
    assert len(idx._objects) == before_len

    # Insert y. It should reuse the next free slot: rid_c
    y, ry = "y", _rect(80, 80, 90, 90)
    assert idx.insert(y, ry) is None
    rid_y = idx._item_to_id[id(y)]
    assert rid_y == rid_c
    assert len(idx._objects) == before_len

    # Removed items do not appear; new items do
    assert a not in idx.intersect(ra)
    assert c not in idx.intersect(rc)
    assert x in idx.intersect(rx)
    assert y in idx.intersect(ry)

    # Free list consumed
    assert idx._free == []


def test_free_slot_reuse_no_growth_under_churn():
    rng = random.Random(123)
    idx = FQTIndex(bbox=WORLD)

    # Insert N items
    n = 200
    items = [f"obj_{i}" for i in range(n)]
    boxes = [
        (_x := rng.uniform(0, 90), _y := rng.uniform(0, 90), _x + 5, _y + 5)
        for _ in range(n)
    ]
    for obj, box in zip(items, boxes):
        idx.insert(obj, box)

    base_len = len(idx._objects)

    # Remove half of them
    removed = []
    for obj, box in zip(items[::2], boxes[::2]):
        idx.remove(obj, box)
        removed.append((obj, box))

    # Reinsert the same count of new items; length should not grow
    for k in range(len(removed)):
        obj = f"new_{k}"
        # use different boxes to ensure spatial removal did not leave stale entries
        x = rng.uniform(0, 90)
        y = rng.uniform(0, 90)
        box = (x, y, x + 3, y + 3)
        idx.insert(obj, box)

    assert len(idx._objects) == base_len

    # None of the removed items should be found
    for obj, box in removed:
        assert obj not in idx.intersect(box)
