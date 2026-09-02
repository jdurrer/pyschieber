import pytest

from pyschieber.rules.trumpf_rules import trumpf_allowed
from pyschieber.trumpf import Trumpf


@pytest.mark.parametrize(
    "trumpf, geschoben, result",
    [
        (Trumpf.OBE_ABE, True, True),
        (Trumpf.OBE_ABE, False, True),
        (Trumpf.SCHIEBEN, True, False),
        (Trumpf.SCHIEBEN, False, True),
    ],
)
def test_trumpf(trumpf, geschoben, result):
    assert trumpf_allowed(chosen_trumpf=trumpf, geschoben=geschoben) == result
