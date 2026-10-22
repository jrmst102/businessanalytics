"""Fit one classroom configuration from the command line and print its results.

Usage examples (developer convenience; the dashboard is the student interface):
    python run_engine.py
    python run_engine.py --model "Regression tree" --parameter 12
    python run_engine.py --model "Neural network" --parameter "32,16"
    python run_engine.py --model "Ensemble regression" --parameter "Weighted average"
"""
import argparse

import models


def parse_parameter(choice, text):
    if text is None:
        return models.PRESETS[choice]['default']
    if choice == 'Neural network':
        return tuple(int(part) for part in text.replace('(', '').replace(')', '').split(','))
    if choice == 'Ensemble regression':
        return text
    return int(text)


def main():
    parser = argparse.ArgumentParser(description='Fit one classroom model configuration.')
    parser.add_argument('--model', default='KNN regression', choices=models.MODEL_CHOICES)
    parser.add_argument('--parameter', default=None,
                        help='Classroom preset, e.g. 15, 6, 100, "32,16", "Equal weights". '
                             'Defaults to the classroom default for the model.')
    args = parser.parse_args()
    parameter = parse_parameter(args.model, args.parameter)

    df = models.load_data()
    print('Checksum matches approved snapshot:', models.dataset_checksum() == models.DATA_SHA256)
    print(models.describe_data(df))
    data = models.prepare_data(df)

    estimator, settings = models.build_model(args.model, parameter)
    print(f'Fitting {args.model} ({settings}) on the development dates...')
    result = models.fit_selected_model(estimator, data)
    scores = result['scores']
    print(f"Fit time: {result['fit_seconds']:.1f} s on {result['development_rows']:,} rows; "
          f"evaluated on {result['test_rows']:,} test rows "
          f"({result['test_start'].date()} to {result['test_end'].date()}).")
    r2 = 'N/A' if scores['R2'] is None else f"{scores['R2']:.3f}"
    mape = 'N/A' if scores['MAPE'] is None else f"{scores['MAPE']:.2f}%"
    print(f"R² {r2} | MSE {scores['MSE']:.2f} | RMSE {scores['RMSE']:.2f} | MAPE {mape} "
          f"({scores['positive_observations']:,} positive-sales observations; "
          f"{scores['zero_excluded_from_mape']:,} zero-sales rows excluded from MAPE)")
    for message in result['warnings']:
        print('Warning:', message)
    if 'training_epochs' in result:
        print('Network training epochs:', result['training_epochs'])

    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    print('Typed example (store 3, Bakery, 2025-10-15):',
          f"{models.predict_one(result['pipeline'], row):.2f} units")
    print(models.run_identity(args.model, settings, data))


if __name__ == '__main__':
    main()
