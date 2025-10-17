from navdict import navdict
from navdict.changed import ChangeTrackingDict


def test_change_tracking():
    ###
    # The first test I ran was to have NavigableDict inherit from ChangeTrackingDict, but that didn't
    # work and changes were not recorded. Second, I tried to have ChangeTrackingDict(x) and use the
    # dot-notation to change values, but that gave me an AttributeError. So, I think I will have to
    # merge the ChangeTrackingDict into the NavigableDict class.
    ###

    print()
    print("-" * 40, " Started Change Tracking Test ", "-" * 40)

    # x = navdict({"A": {"B": [1, 2, 3, 4], "C": int}})
    x = ChangeTrackingDict({"A": {"B": [1, 2, 3, 4], "C": int}})

    x.reset_tracking()

    print(f"Initial: {x.changed}")
    assert not x.changed

    # x["A"]["C"] = bool
    x.A.C = bool
    print(f'After changing x["A"]["C"] = bool -> {x.changed}')
    assert x.changed

    # x["A"]["B"][1] = 0
    x.A.B[1] = 0
    print(f'After changing x["A"]["B"][1] = 0 -> {x.changed}')
    assert x.changed

    print("-" * 40, " Finished Change Tracking Test ", "-" * 40)
