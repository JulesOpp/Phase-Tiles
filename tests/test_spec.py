import numpy as np

from phasetiles.spec import Axis, DiagramSpec, Display, default_spec


def test_axis_values_include_the_stop():
    assert np.allclose(Axis("J1", -1, 1, 0.5).values(),
                       [-1, -.5, 0, .5, 1])


def test_default_spec_is_valid():
    errors, warnings = default_spec().validate()
    assert errors == [] and warnings == []


def test_a_step_that_does_not_divide_the_range_warns_and_stops_short():
    s = default_spec().replace(x=Axis("J1", -1, 1, 0.3))
    errors, warnings = s.validate()
    assert errors == []
    assert "last tile at 0.8" in warnings[0]
    assert np.isclose(s.x.values()[-1], 0.8)


def test_zero_or_negative_steps_and_reversed_ranges_are_errors():
    for ax in (Axis("J1", -1, 1, 0), Axis("J1", -1, 1, -0.1),
               Axis("J1", 1, -1, 0.1)):
        errors, _ = default_spec().replace(x=ax).validate()
        assert errors, ax


def test_both_axes_on_one_parameter_is_an_error():
    s = default_spec().replace(y=Axis("J1", -1, 1, 0.1))
    assert "same parameter" in " ".join(s.validate()[0])


def test_an_axis_not_in_the_hamiltonian_is_an_error():
    s = default_spec().replace(y=Axis("J3", -1, 1, 0.1))
    assert "J3 is not a term" in " ".join(s.validate()[0])


def test_temperature_must_be_positive_fixed_or_varied():
    s = default_spec().replace(fixed=(("T", 0.0),))
    assert "T must be > 0" in " ".join(s.validate()[0])
    s = default_spec().replace(x=Axis("T", 0, 1, 0.1))
    assert "T must be > 0" in " ".join(s.validate()[0])


def test_too_many_tiles_is_an_error_that_gives_the_count():
    s = default_spec().replace(x=Axis("J1", -1, 1, 0.01),
                               y=Axis("J2", -1, 1, 0.01))
    assert "40401 tiles" in " ".join(s.validate()[0])


def test_params_at_merges_axes_and_fixed_values():
    p = default_spec().params_at(-0.5, 0.25)
    # H is remembered in `fixed` but is not a term until ticked
    assert p == {"J1": -0.5, "J2": 0.25, "T": 0.5}


def test_display_changes_do_not_change_the_mc_key():
    s = default_spec()
    t = s.replace(display=Display(centre="half", dyn=3.0))
    assert s.mc_key() == t.mc_key()
    assert s.mc_key() != s.replace(net="kgm").mc_key()


def test_round_trips_through_json():
    s = default_spec()
    assert DiagramSpec.from_json(s.to_json()) == s


def test_default_supercell_is_about_48_over_root_nsub_in_twelves():
    s = default_spec()
    assert s.n_cells(1) == 48 and s.n_cells(3) == 24
    assert s.n_cells(24) == 12
