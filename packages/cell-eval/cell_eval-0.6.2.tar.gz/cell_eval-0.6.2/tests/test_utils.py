from cell_eval.data import build_random_anndata
from cell_eval.utils import guess_is_lognorm


def test_is_lognorm_true():
    data = build_random_anndata(normlog=True)
    assert guess_is_lognorm(data)


def test_is_lognorm_false():
    data = build_random_anndata(normlog=False)
    assert not guess_is_lognorm(data)
