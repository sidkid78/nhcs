import collect_dataset as cd, pathlib, asyncio 

cd.OUT_CSV=pathlib.Path('data/nhcs_run_007.csv')
cd.LEDGER_PATH='data/nhcs_run_007.db'
cd.RNG_SEED=123 

asyncio.run(cd.collect())