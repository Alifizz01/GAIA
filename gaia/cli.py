"""gaia command line.

    gaia studio                        open the desktop GUI
    gaia serve [--port 8780]           REST API + Studio in a browser
    gaia simulate --params JSON        one PyBaMM cell run, prints GAIA_RESULT:{json}
    gaia benchmark [--chemistry NMC]   SOC estimator accuracy against PyBaMM truth
    gaia ocv                           regenerate the OCV tables
"""
import argparse
import json
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gaia", description="Battery management system simulator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("studio", "serve"):
        p = sub.add_parser(name)
        p.add_argument("--port", type=int, default=8780)
    s = sub.add_parser("simulate", help="run one cell simulation from JSON parameters")
    s.add_argument("--params", default="{}",
                   help='e.g. {"chemistry": "LFP", "model": "SPMe", "c_rate": 1, "thermal": true}')
    b = sub.add_parser("benchmark", help="SOC estimators against PyBaMM truth")
    b.add_argument("--chemistry", default="NMC")
    sub.add_parser("ocv", help="regenerate the OCV tables from PyBaMM")
    a = ap.parse_args(argv)

    if a.cmd == "studio":
        from gaia.studio_app import main as studio
        studio(a.port)
    elif a.cmd == "serve":
        from gaia.server import serve
        serve(a.port)
    elif a.cmd == "simulate":
        from gaia.api import cell_simulate
        print("GAIA_RESULT:" + json.dumps(cell_simulate(json.loads(a.params))))
    elif a.cmd == "benchmark":
        from gaia.soc_benchmark import run_benchmark
        r = run_benchmark(a.chemistry)
        print(f"{a.chemistry}: SOC RMSE after 10 min (start guess {r['conditions']['initial_soc_guess']:.0f} %)")
        for name, value in r["rmse_after_10min"].items():
            print(f"  {name:<17} {value:6.2f} %")
    elif a.cmd == "ocv":
        from gaia import ocv
        for chem in ocv.CHEMISTRIES:
            ocv.generate(chem)
            print("wrote", chem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
