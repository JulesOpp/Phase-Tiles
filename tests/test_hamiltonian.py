from phasetiles.hamiltonian import Hamiltonian, Term, default


def test_terms_name_themselves_by_shell():
    assert Term("pair", 1).symbol == "J1"
    assert Term("pair", 3).label == "NNNN"
    assert Term("field").symbol == "H"


def test_symbols_always_end_with_temperature():
    h = Hamiltonian(terms=(Term("pair", 1), Term("field")))
    assert h.symbols() == ["J1", "H", "T"]
    assert h.nshell() == 1


def test_formula_reads_like_the_energy():
    h = Hamiltonian(terms=(Term("pair", 1), Term("pair", 2),
                           Term("field")))
    assert h.formula() == ("E = −J1 Σ_NN sᵢsⱼ − J2 Σ_NNN sᵢsⱼ"
                           " − H Σ sᵢ")


def test_round_trips_through_a_dict():
    h = default()
    assert Hamiltonian.from_dict(h.to_dict()) == h


def test_nshell_counts_up_to_the_highest_shell_even_with_gaps():
    h = Hamiltonian(terms=(Term("pair", 1), Term("pair", 3)))
    assert h.nshell() == 3
