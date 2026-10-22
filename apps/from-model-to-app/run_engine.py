"""Run the full classroom workflow from the command line and print the results.

Usage: python run_engine.py
This is a developer convenience and a quick way to see the engine without the
dashboard. It performs the same steps as the notebook, in the same order.
"""
import time

import models


def main():
    df = models.load_data()
    print('Checksum matches approved snapshot:', models.dataset_checksum() == models.DATA_SHA256)
    print(models.describe_data(df))
    data = models.prepare_data(df)
    print(data['partitions'].to_string(index=False))

    started = time.perf_counter()
    candidates = models.run_classroom_comparison(
        data, progress=lambda i, n, name: print(f'  [{i}/{n}] {name}'))
    print(f'Full comparison: {time.perf_counter() - started:.1f} s')

    board = models.leaderboard(candidates)
    print(board.drop(columns=['Settings']).round(3).to_string(index=False))
    for name, c in candidates.items():
        if c['warnings']:
            print(f'Warnings for {name}:', c['warnings'])
        if 'training_epochs' in c:
            print(f'{name} training epochs: {c["training_epochs"]}')

    selected = models.select_model(candidates)
    gain = models.ensemble_gain(candidates)
    print('Selected:', selected, '| Family winners:', models.family_winners(candidates))
    print('Ensemble gain:', gain)
    print(models.residual_correlations(candidates, models.family_winners(candidates), data).round(3))

    final = models.finalize_model(selected, models.clone(candidates[selected]['specification']), data)
    print(final['test_results'].round(3).to_string(index=False))
    print(final['summary'].round(3).to_string(index=False))
    print(final['store_diagnostics'].round(2))
    print(final['category_diagnostics'].head(5).round(2))
    print(models.managerial_briefing(final, candidates[selected]['family'], gain))

    row = models.make_prediction_row('1', 'Bakery', '2025-10-15')
    started = time.perf_counter()
    print('Typed example prediction:', models.predict_one(final['final_model'], row),
          f'({(time.perf_counter() - started) * 1000:.0f} ms)')
    print(models.run_identity(selected, candidates[selected]['settings'], data, 'final'))


if __name__ == '__main__':
    main()
