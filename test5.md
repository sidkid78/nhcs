```log
(alien) PS C:\Users\sidki\source\repos\alien> python -m collect_dataset                                                   
2026-07-04 13:13:48,038 [INFO] nhcs.collect - Initialising pipeline components...
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
2026-07-04 13:13:48,461 [WARNING] huggingface_hub.utils._http - Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 7505.96it/s]
2026-07-04 13:13:50,247 [INFO] nhcs.layer1_genesis.aian - AIAN loaded encoder 'all-MiniLM-L6-v2'.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 6943.43it/s]
2026-07-04 13:13:52,077 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger opened at data\nhcs_run_007.db.
2026-07-04 13:13:54,771 [INFO] nhcs.layer2_tmft.controller - Spectral forms gs=12: 672 interior pts, achievable C in [0.002, 68.406]
2026-07-04 13:13:54,773 [INFO] nhcs.layer3_crim.biometrics_lsl - BiometricsLSL: synthetic subject mode.
2026-07-04 13:13:54,775 [INFO] nhcs.collect - Starting collection run - target: 10 concepts
2026-07-04 13:14:01,365 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:01,554 [INFO] nhcs.layer1_genesis.aian - AIAN kept 1/20 candidates.
2026-07-04 13:14:01,554 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 1/1.
2026-07-04 13:14:01,571 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:01,612 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 0d4fa074-f19d-4d00-abda-e4f20d39c3ed.
2026-07-04 13:14:01,613 [WARNING] nhcs.layer2_tmft.topology_to_field - TPMM freq 10.83 Hz outside RSR [15.0-40.0] for betti=[9, 1, 0]. Clamping.
2026-07-04 13:14:01,613 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=17.801 achieved=17.800761 (exact) bracket=[0.002, 68.406] s=0.260 variant=1 freq=15.0Hz max|I|=10.0A
2026-07-04 13:14:01,925 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=1 target_c=17.80 achieved=17.8008 err=0.0% B=0.07mT freq=15.0Hz [0.31s]
2026-07-04 13:14:01,928 [INFO] nhcs.collect - [ 1/10] concept=0d4fa074  b=[9,1,0]  novelty=0.608  freq=15.0Hz  BHI=0.917  CLI=0.099  SDR=0.2667  (7.2s)
2026-07-04 13:14:07,954 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:08,053 [INFO] nhcs.layer1_genesis.aian - AIAN kept 4/20 candidates.
2026-07-04 13:14:08,053 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:08,053 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:08,054 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,054 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,054 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:08,054 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,054 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,054 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,055 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:08,056 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:08,056 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:08,056 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/4.
2026-07-04 13:14:08,072 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:08,099 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept eae90405-6e8e-47a5-899d-d9078088b669.
2026-07-04 13:14:08,099 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=26.235 achieved=26.235046 (exact) bracket=[0.002, 68.406] s=0.383 variant=2 freq=17.9Hz max|I|=10.0A
2026-07-04 13:14:08,336 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=2 target_c=26.24 achieved=26.2350 err=0.0% B=0.06mT freq=17.9Hz [0.24s]
2026-07-04 13:14:08,339 [INFO] nhcs.collect - [ 2/10] concept=eae90405  b=[6,2,0]  novelty=0.638  freq=17.9Hz  BHI=0.960  CLI=0.140  SDR=0.3076  (6.4s)
2026-07-04 13:14:14,902 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:14,939 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 13:14:14,939 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:14,939 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:14,940 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,940 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:14:14,940 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:14:14,940 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,940 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:14:14,940 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:14:14,941 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,941 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:14,941 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:14,941 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,941 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:14:14,941 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:14:14,942 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,942 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:14,942 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:14:14,942 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:14:14,942 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,942 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:14,943 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:14,943 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:14,943 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:14,943 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:14,943 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5.
2026-07-04 13:14:14,958 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:15,013 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept f206760b-ca21-4813-bf29-3c202bf078bf.
2026-07-04 13:14:15,013 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 13:14:15,252 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.24s] 
2026-07-04 13:14:15,256 [INFO] nhcs.collect - [ 3/10] concept=f206760b  b=[5,3,0]  novelty=0.603  freq=23.1Hz  BHI=0.974  CLI=0.152  SDR=0.0000  (6.9s)
2026-07-04 13:14:22,594 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:22,644 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 13:14:22,644 [INFO] nhcs.layer1_genesis.search - [10, 1, 0]
2026-07-04 13:14:22,644 [INFO] nhcs.layer1_genesis.search - [10.  1.  0.]
2026-07-04 13:14:22,644 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,644 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,645 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [10, 1, 0]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,646 [INFO] nhcs.layer1_genesis.search - [10, 1, 0]
2026-07-04 13:14:22,647 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:22,647 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:22,647 [INFO] nhcs.layer1_genesis.search - [8, 2, 1]
2026-07-04 13:14:22,647 [INFO] nhcs.layer1_genesis.search - [10, 1, 0]
2026-07-04 13:14:22,647 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5.
2026-07-04 13:14:22,665 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:22,714 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept a14d9f33-c090-4563-89e6-6a9498bd9eb0.
2026-07-04 13:14:22,715 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=36.778 achieved=36.777903 (exact) bracket=[5.149, 68.406] s=0.500 variant=4 freq=27.2Hz max|I|=10.0A
2026-07-04 13:14:22,949 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=4 target_c=36.78 achieved=36.7779 err=0.0% B=0.04mT freq=27.2Hz [0.23s]
2026-07-04 13:14:22,953 [INFO] nhcs.collect - [ 4/10] concept=a14d9f33  b=[8,2,1]  novelty=0.619  freq=27.2Hz  BHI=0.976  CLI=0.149  SDR=0.0000  (7.7s)
2026-07-04 13:14:29,308 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:29,368 [INFO] nhcs.layer1_genesis.aian - AIAN kept 8/20 candidates.
2026-07-04 13:14:29,369 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:29,369 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:29,369 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,369 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:29,369 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:29,370 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,370 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:29,370 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:29,370 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,370 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:29,370 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:29,371 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,371 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,371 [INFO] nhcs.layer1_genesis.search - [8. 2. 0.]
2026-07-04 13:14:29,371 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,371 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:29,371 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [7, 2, 0]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [7. 2. 0.]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:29,372 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,373 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,373 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:29,373 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:29,373 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,373 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,373 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:29,374 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:29,374 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,374 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,374 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:29,374 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:29,375 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,375 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,375 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:29,375 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:29,375 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,375 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,376 [INFO] nhcs.layer1_genesis.search - [7, 2, 0]
2026-07-04 13:14:29,376 [INFO] nhcs.layer1_genesis.search - [7. 2. 0.]
2026-07-04 13:14:29,376 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:14:29,376 [INFO] nhcs.layer1_genesis.search - [8, 2, 0]
2026-07-04 13:14:29,376 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/8.
2026-07-04 13:14:29,393 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:29,403 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 85c5bf49-932c-4eb2-8138-3cd3d1f1586e.
2026-07-04 13:14:29,404 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 13:14:29,676 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.27s]
2026-07-04 13:14:29,679 [INFO] nhcs.collect - [ 5/10] concept=85c5bf49  b=[6,3,0]  novelty=0.624  freq=23.1Hz  BHI=0.979  CLI=0.154  SDR=0.0000  (6.7s)
2026-07-04 13:14:36,406 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:36,425 [INFO] nhcs.layer1_genesis.aian - AIAN kept 4/20 candidates.
2026-07-04 13:14:36,426 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,426 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:36,426 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,426 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,426 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:36,427 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,427 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,427 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:36,427 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,427 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,427 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:36,428 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/4.
2026-07-04 13:14:36,447 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:36,458 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept b8885932-4e00-4604-95ec-ac4f00b2f1c8.
2026-07-04 13:14:36,458 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=26.235 achieved=26.235046 (exact) bracket=[0.002, 68.406] s=0.383 variant=2 freq=17.9Hz max|I|=10.0A
2026-07-04 13:14:36,708 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=2 target_c=26.24 achieved=26.2350 err=0.0% B=0.06mT freq=17.9Hz [0.25s]
2026-07-04 13:14:36,712 [INFO] nhcs.collect - [ 6/10] concept=b8885932  b=[6,2,0]  novelty=0.620  freq=17.9Hz  BHI=0.973  CLI=0.150  SDR=0.3092  (7.0s)
2026-07-04 13:14:43,523 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:43,591 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 13:14:43,592 [INFO] nhcs.layer1_genesis.search - [8, 0, 1]
2026-07-04 13:14:43,592 [INFO] nhcs.layer1_genesis.search - [8. 0. 1.]
2026-07-04 13:14:43,592 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,593 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:43,593 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:43,593 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,593 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:43,594 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:43,594 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,594 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:43,594 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:43,594 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,594 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [8, 0, 1]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,595 [INFO] nhcs.layer1_genesis.search - [8, 0, 1]
2026-07-04 13:14:43,596 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:43,596 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:43,596 [INFO] nhcs.layer1_genesis.search - [6, 4, 0]
2026-07-04 13:14:43,596 [INFO] nhcs.layer1_genesis.search - [8, 0, 1]
2026-07-04 13:14:43,596 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5.
2026-07-04 13:14:43,614 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:43,626 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept c55047f6-4d7a-47a4-bd5a-a2badc5c8daa.
2026-07-04 13:14:43,626 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=36.778 achieved=36.777903 (exact) bracket=[5.149, 68.406] s=0.500 variant=4 freq=27.2Hz max|I|=10.0A
2026-07-04 13:14:43,881 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=4 target_c=36.78 achieved=36.7779 err=0.0% B=0.04mT freq=27.2Hz [0.26s]
2026-07-04 13:14:43,885 [INFO] nhcs.collect - [ 7/10] concept=c55047f6  b=[6,4,0]  novelty=0.632  freq=27.2Hz  BHI=0.979  CLI=0.153  SDR=0.0000  (7.2s)
2026-07-04 13:14:49,781 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:49,815 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 13:14:49,815 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:49,816 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:49,816 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,816 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:49,816 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:49,816 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:49,817 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [6, 2, 0]
2026-07-04 13:14:49,818 [INFO] nhcs.layer1_genesis.search - [6. 2. 0.]
2026-07-04 13:14:49,819 [INFO] nhcs.layer1_genesis.search - [4, 4, 0]
2026-07-04 13:14:49,819 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:49,819 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5.
2026-07-04 13:14:49,833 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:49,844 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 741d7a65-4525-41f8-b299-1523241cae93.
2026-07-04 13:14:49,845 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=36.778 achieved=36.777903 (exact) bracket=[5.149, 68.406] s=0.500 variant=4 freq=27.2Hz max|I|=10.0A
2026-07-04 13:14:50,097 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=4 target_c=36.78 achieved=36.7779 err=0.0% B=0.04mT freq=27.2Hz [0.25s]
2026-07-04 13:14:50,102 [INFO] nhcs.collect - [ 8/10] concept=741d7a65  b=[4,4,0]  novelty=0.608  freq=27.2Hz  BHI=0.978  CLI=0.165  SDR=0.0000  (6.2s)
2026-07-04 13:14:56,015 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:14:56,029 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 13:14:56,030 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:56,030 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:56,030 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,030 [INFO] nhcs.layer1_genesis.search - [9, 1, 0]
2026-07-04 13:14:56,030 [INFO] nhcs.layer1_genesis.search - [9. 1. 0.]
2026-07-04 13:14:56,031 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,031 [INFO] nhcs.layer1_genesis.search - [6, 1, 0]
2026-07-04 13:14:56,031 [INFO] nhcs.layer1_genesis.search - [6. 1. 0.]
2026-07-04 13:14:56,031 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,031 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,031 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:56,032 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,032 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:14:56,032 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:14:56,032 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,032 [INFO] nhcs.layer1_genesis.search - [9, 1, 0]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [6, 1, 0]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [6. 1. 0.]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [9, 1, 0]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [5. 3. 0.]
2026-07-04 13:14:56,033 [INFO] nhcs.layer1_genesis.search - [5, 3, 0]
2026-07-04 13:14:56,034 [INFO] nhcs.layer1_genesis.search - [9, 1, 0]
2026-07-04 13:14:56,034 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5.
2026-07-04 13:14:56,047 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:14:56,059 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 1bf67855-dff1-46e2-a429-326d6b10de15.
2026-07-04 13:14:56,059 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 13:14:56,353 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.29s]
2026-07-04 13:14:56,356 [INFO] nhcs.collect - [ 9/10] concept=1bf67855  b=[5,3,0]  novelty=0.612  freq=23.1Hz  BHI=0.978  CLI=0.159  SDR=0.0000  (6.2s)
2026-07-04 13:15:02,837 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 13:15:02,842 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 13:15:02,843 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:15:02,843 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:15:02,843 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,843 [INFO] nhcs.layer1_genesis.search - [6, 1, 0]
2026-07-04 13:15:02,843 [INFO] nhcs.layer1_genesis.search - [6. 1. 0.]
2026-07-04 13:15:02,844 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,844 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:15:02,844 [INFO] nhcs.layer1_genesis.search - [8. 1. 0.]
2026-07-04 13:15:02,844 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,844 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [7, 1, 0]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [7. 1. 0.]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:15:02,845 [INFO] nhcs.layer1_genesis.search - [6, 1, 0]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [6. 1. 0.]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [5, 2, 0]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [5. 2. 0.]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [6, 3, 0]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - [8, 1, 0]
2026-07-04 13:15:02,846 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5.
2026-07-04 13:15:02,862 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 13:15:02,873 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 6f710d63-eb5c-4d39-b7fe-fa3669516927.
2026-07-04 13:15:02,873 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 13:15:03,119 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.25s]
2026-07-04 13:15:03,123 [INFO] nhcs.collect - [10/10] concept=6f710d63  b=[6,3,0]  novelty=0.657  freq=23.1Hz  BHI=0.983  CLI=0.163  SDR=0.0000  (6.8s)
2026-07-04 13:15:03,124 [INFO] nhcs.collect -
2026-07-04 13:15:03,124 [INFO] nhcs.collect - === COLLECTION COMPLETE ===
2026-07-04 13:15:03,124 [INFO] nhcs.collect - Concepts collected : 10/10
2026-07-04 13:15:03,124 [INFO] nhcs.collect - Total attempts     : 10
2026-07-04 13:15:03,125 [INFO] nhcs.collect - Ledger size        : 30
2026-07-04 13:15:03,125 [INFO] nhcs.collect - Output             : data\nhcs_run_007.csv
2026-07-04 13:15:03,126 [INFO] nhcs.collect - ==================================================
2026-07-04 13:15:03,126 [INFO] nhcs.collect -
2026-07-04 13:15:03,127 [INFO] nhcs.collect - TOPOLOGY  beta1: 1-4 (mean 2.7)
2026-07-04 13:15:03,127 [INFO] nhcs.collect - NOVELTY   aggregate: 0.603-0.657 (mean 0.622)
2026-07-04 13:15:03,127 [INFO] nhcs.collect - SDR       range: 0.0000-0.3092 (mean 0.0883)
2026-07-04 13:15:03,127 [INFO] nhcs.collect - BHI       range: 0.917-0.983
2026-07-04 13:15:03,128 [INFO] nhcs.collect - CLI mean  range: 0.099-0.165
2026-07-04 13:15:03,128 [INFO] nhcs.collect -
2026-07-04 13:15:03,128 [INFO] nhcs.collect - PRIME1 distribution:
2026-07-04 13:15:03,128 [INFO] nhcs.collect -   HERE                   7/10
2026-07-04 13:15:03,128 [INFO] nhcs.collect -   BELOW                  2/10
2026-07-04 13:15:03,128 [INFO] nhcs.collect -   FAR                    1/10








