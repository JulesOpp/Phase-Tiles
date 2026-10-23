"""Compute the missing tiles of a spec, in processes.

spawn, not fork: fork is unavailable on Windows and unsafe on macOS
with Qt loaded, and a frozen app needs freeze_support() in main (see
CLAUDE.md).  Workers default to 2 because each holds a lattice and
its snapshots and the target machines have 16 GB.  A stop request
cancels queued tiles and drops running ones: nothing half-done is
ever stored.
"""
import multiprocessing as mp
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass

import numpy as np

from phasetiles import mc, nets, scattering, tiling
from phasetiles.store import TileResult


@dataclass(frozen=True)
class Job:
    net: str
    nshell: int
    n: int
    params: tuple            # sorted (name, value) pairs, picklable
    mc: object


_LAT = {}
_STOP = None          # the pool's stop Event, in each worker


def _init_worker(stop):
    global _STOP
    _STOP = stop


def _pool_tile(job):
    # the worker's own copy of the stop flag: without it a stopped
    # run (or closing the window) waited for every running tile
    return compute_tile(job, _STOP.is_set)


def _lattice(net, n, nshell):
    k = (net.name, n, nshell)
    if k not in _LAT:
        _LAT.clear()
        _LAT[k] = mc.Lattice(net, n, nshell)
    return _LAT[k]


def compute_tile(job, should_stop=None):
    net = nets.Net(job.net, nshell=max(job.nshell, 1))
    lat = _lattice(net, job.n, job.nshell)
    p = dict(job.params)
    J = [p.get(f"J{k + 1}", 0.0) for k in range(job.nshell)]
    r = mc.run_mc(lat, J, p.get("H", 0.0), p["T"], job.mc.anneal,
                  job.mc.equil, job.mc.snaps, job.mc.seed, should_stop)
    C = scattering.correlations(lat, r.snaps)
    phi2 = scattering.order_params(
        scattering.correlations(lat, r.snaps, subtract_mean=True))
    absm = float(np.mean([abs(s.mean()) for s in r.snaps]))
    energy = float(r.energy[job.mc.anneal:].mean())
    return TileResult(p, C.astype(np.complex64), phi2, r.snaps[-1],
                      r.drift, absm, energy)


def jobs_for(spec, store):
    net = nets.Net(spec.net, nshell=1)
    n = spec.n_cells(net.nsub)
    B, _ = tiling.recip(net)
    out = []
    for t in tiling.tile_centres(B, spec.x, spec.y):
        p = spec.params_at(t.x, t.y)
        if not store.has(spec, p):
            out.append(Job(spec.net, spec.hamiltonian.nshell(), n,
                           tuple(sorted(p.items())), spec.mc))
    return out


def _serial(spec, store, jobs, on_tile, stop):
    done = 0
    for j in jobs:
        if stop():
            break
        try:
            r = compute_tile(j, stop)
        except mc.Cancelled:
            break
        store.put(spec, r.params, r)
        done += 1
        if on_tile:
            on_tile(r)
    return done


def run_tiles(spec, store, workers=2, on_tile=None, should_stop=None):
    """Compute every missing tile; returns how many were stored."""
    jobs = jobs_for(spec, store)
    stop = should_stop or (lambda: False)
    if workers <= 1 or len(jobs) <= 1:
        return _serial(spec, store, jobs, on_tile, stop)
    done = 0
    it = iter(jobs)
    ctx = mp.get_context("spawn")
    halt = ctx.Event()
    ex = ProcessPoolExecutor(workers, mp_context=ctx,
                             initializer=_init_worker, initargs=(halt,))
    try:
        pending = {ex.submit(_pool_tile, j)
                   for _, j in zip(range(2 * workers), it, strict=False)}
        while pending and not stop():
            fin, pending = wait(pending, timeout=0.5,
                                return_when=FIRST_COMPLETED)
            for f in fin:
                r = f.result()
                store.put(spec, r.params, r)
                done += 1
                if on_tile:
                    on_tile(r)
                nxt = next(it, None)
                if nxt is not None:
                    pending.add(ex.submit(_pool_tile, nxt))
    finally:
        halt.set()      # running tiles raise Cancelled; none is stored
        ex.shutdown(wait=True, cancel_futures=True)
    return done
