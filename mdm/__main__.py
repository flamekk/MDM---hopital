import argparse
import json
from pathlib import Path
from .demo import generate, import_legacy
from .pipeline import run
from . import store


def main():
    parser = argparse.ArgumentParser(description="MDM hospitalier : démonstration reproductible")
    parser.add_argument('action', choices=['demo', 'hospital-demo', 'run', 'verify', 'api', 'import-patients'])
    parser.add_argument('--workspace', type=Path, default=Path('workspace'))
    parser.add_argument('--method', choices=['exact', 'weighted', 'probabilistic'], default='weighted')
    parser.add_argument('--base-run')
    parser.add_argument('--no-evaluation', action='store_true')
    parser.add_argument('--size', type=int, default=48)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--scenario', choices=['S1_5pct', 'S2_15pct', 'S3_30pct'], default='S1_5pct')
    args = parser.parse_args()
    try:
        if args.action == 'demo':
            generate(args.workspace, args.size)
            result = run(args.workspace, args.method, evaluate=not args.no_evaluation)
        elif args.action == 'hospital-demo':
            from .hospital import SCENARIOS, generate_hospital
            for scenario in SCENARIOS:
                target = args.workspace / scenario
                if not (target / 'sources').exists():
                    generate_hospital(target, args.size, scenario)
                result = run(target, args.method, evaluate=not args.no_evaluation)
                print(json.dumps(dict(scenario=scenario, run_id=result['run_id'], records=len(result['xrefs']), masters=len(result['masters']))))
            return 0
        elif args.action == 'run':
            result = run(args.workspace, args.method, args.base_run, not args.no_evaluation)
        elif args.action == 'import-patients':
            import_legacy(args.workspace, Path(__file__).resolve().parents[1] / 'patient_mdm_synthetic_dataset', args.scenario)
            result = run(args.workspace, args.method, evaluate=not args.no_evaluation)
        elif args.action == 'verify':
            valid = store.verify(args.workspace)
            print(json.dumps({'audit_valid': valid, 'runs': len(store.list_runs(args.workspace))}))
            return 0 if valid else 1
        else:
            from .api import serve
            serve(args.workspace, args.port)
            return 0
        print(json.dumps(dict(run_id=result['run_id'], records=len(result['xrefs']), masters=len(result['masters']),
                              review_cases=sum(p['decision'] == 'REVIEW' for p in result['pairs']),
                              output=str(args.workspace / 'runs' / result['run_id'])), indent=2))
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Erreur : {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
