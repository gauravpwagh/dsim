"""Command-line entry point: `iidsim run --corridor sprd_vzm --dataset p_g_sprd_vzm_2days`.

Replaces editing final_sim_sj_4aug.py's hardcoded corridor import to switch datasets.
"""
import argparse

from iidsim.engine import run_simulation
from iidsim.schedules import available_corridors


def main(argv=None):
    parser = argparse.ArgumentParser(prog="iidsim")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="run one simulation end-to-end")
    run_p.add_argument(
        "--dataset", required=True,
        help=f"which train schedule to load, one of: {', '.join(available_corridors())}",
    )
    run_p.add_argument(
        "--corridor", required=True, choices=["psa_ktv", "sprd_vzm", "krdl_ktv"],
        help="which corridor's station order/distances to chart against",
    )
    run_p.add_argument("--output-dir", default="output_files")
    run_p.add_argument("--no-halt-deviation", action="store_true")
    run_p.add_argument("--no-speed-randomness", action="store_true")

    list_p = sub.add_parser("list-datasets", help="list available train schedules")

    args = parser.parse_args(argv)

    if args.command == "list-datasets":
        for name in available_corridors():
            print(name)
        return

    result = run_simulation(
        args.dataset,
        args.corridor,
        output_dir=args.output_dir,
        use_halt_deviation=not args.no_halt_deviation,
        use_speed_randomness=not args.no_speed_randomness,
    )
    print(f"Excel report:   {result['excel_filename']}")
    print(f"Chart PDF:      {result['chart_filename']}")
    print(f"Animator JSON:  {result['animator_filename']}")


if __name__ == "__main__":
    main()
