import numpy as np

from phasetiles import classify, nets


def _phi(n, hits):
    p = np.zeros((n, n))
    for (a, b), v in hits.items():
        p[a, b] = v
    return p


def test_stripe_domains_of_both_orientations_are_one_phase():
    net = nets.Net("sql", nshell=1)
    q = classify.canonical_q(net, 24)
    ph = classify.classify(_phi(24, {(12, 0): .5, (0, 12): .5}), 0.0,
                           24, q, 0.3, 1)
    assert ph.label == "q = (0, 1/2)"
    assert sorted(ph.star) == [(0, 12), (12, 0)]


def test_domain_broadened_peaks_snap_to_the_commensurate_q():
    net = nets.Net("sql", nshell=1)
    q = classify.canonical_q(net, 48)
    ph = classify.classify(_phi(48, {(1, 24): .8}), 0.0, 48, q, 0.3, 1)
    assert ph.label == "q = (0, 1/2)"


def test_small_order_is_disordered_and_magnetisation_is_ferro():
    net = nets.Net("sql", nshell=1)
    q = classify.canonical_q(net, 24)
    assert classify.classify(_phi(24, {(3, 5): .01}), 0.05, 24, q,
                             0.3, 1).label == "disordered"
    ph = classify.classify(_phi(24, {}), 0.9, 24, q, 0.3, 1)
    assert ph.label == "ferro (q = 0)" and ph.star == [(0, 0)]
