import pytest
from epmatools import mindb


def test_molprop(data):
    assert data.molprop().sum.sum() == pytest.approx(22.091604439186142)


def test_cat_number(data):
    assert data.cat_number.sum.sum() == pytest.approx(28.14265725481788)


def test_oxy_number(data):
    assert data.oxy_number.sum.sum() == pytest.approx(43.57257550837694)


def test_mineral_formula(data):
    g = data.search("g")
    grt = mindb.Garnet_Fe2()
    apfu = g.apfu(grt)
    assert apfu.mineral_apfu().sum.mean() == pytest.approx(8.0)
