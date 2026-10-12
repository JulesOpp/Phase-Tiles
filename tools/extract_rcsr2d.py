"""Write phasetiles/data/rcsr2d.cgd: the 2D entries of an RCSR .cgd.

The full RCSR file is 1.9 MB of mostly 3D nets this app never reads;
the 2D entries (plane-group GROUP lines) are what ships.  Run against
RCSRnets-2019-06-01.cgd; see data/PROVENANCE.md.

usage: python tools/extract_rcsr2d.py FULL.cgd
"""
import pathlib
import sys

PLANE = {"p1", "p2", "pm", "pg", "cm", "p2mm", "p2mg", "p2gg", "c2mm",
         "p4", "p4mm", "p4gm", "p3", "p3m1", "p31m", "p6", "p6mm"}
OUT = (pathlib.Path(__file__).resolve().parent.parent / "phasetiles"
       / "data" / "rcsr2d.cgd")


def main(src):
    keep, block = [], []
    for line in open(src, encoding="utf-8"):
        block.append(line)
        if line.strip() == "END":
            grp = [x.split()[1] for x in block
                   if x.split()[:1] == ["GROUP"]]
            named = any(x.split()[:1] == ["NAME"] for x in block)
            if grp and grp[0] in PLANE and named:
                keep += block + ["\n"]
            block = []
    OUT.write_text("".join(keep), encoding="utf-8")
    print("wrote", OUT, sum(x.split()[:1] == ["NAME"] for x in keep),
          "nets")


if __name__ == "__main__":
    main(sys.argv[1])
