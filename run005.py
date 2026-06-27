import collect_dataset as cd, pathlib, asyncio, logging

# Suppress verbose logging
for lg in ['sentence_transformers','httpx','huggingface_hub',
           'nhcs.layer1_genesis.rse','nhcs.layer1_genesis.search']:
    logging.getLogger(lg).setLevel(logging.ERROR)

cd.OUT_CSV    = pathlib.Path('data/nhcs_run_005.csv')
cd.LEDGER_PATH = 'data/nhcs_run_005.db'
cd.RNG_SEED   = 42
cd.N_CONCEPTS  = 10
cd.N_CRIM_STEPS = 20
cd.GRID_SIZE   = 8

asyncio.run(cd.collect())
