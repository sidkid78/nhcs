```log
(alien) PS C:\Users\sidki\source\repos\alien> python -m collect_dataset
2026-07-04 14:10:54,660 [INFO] nhcs.collect - Initialising pipeline components...
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
2026-07-04 14:10:55,107 [WARNING] huggingface_hub.utils._http - Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 7375.89it/s]
2026-07-04 14:10:56,553 [INFO] nhcs.layer1_genesis.aian - AIAN loaded encoder 'all-MiniLM-L6-v2'.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 5533.10it/s]
2026-07-04 14:10:58,119 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger opened at data\nhcs_run_007.db.
2026-07-04 14:11:00,386 [INFO] nhcs.layer2_tmft.controller - Spectral forms gs=12: 672 interior pts, achievable C in [0.002, 68.406]
2026-07-04 14:11:00,388 [INFO] nhcs.layer3_crim.biometrics_lsl - BiometricsLSL: synthetic subject mode.
2026-07-04 14:11:00,390 [INFO] nhcs.collect - Starting collection run - target: 10 concepts
2026-07-04 14:11:06,765 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:06,928 [INFO] nhcs.layer1_genesis.aian - AIAN kept 1/20 candidates.
2026-07-04 14:11:06,928 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch: pool collapsed to 1 unique signature (RSE produced no topological diversity this round).
2026-07-04 14:11:06,945 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:06,959 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept e357e1a5-3a3d-45a8-8144-c2dcf3542ced.
2026-07-04 14:11:06,960 [WARNING] nhcs.layer2_tmft.topology_to_field - TPMM freq 10.83 Hz outside RSR [15.0-40.0] for betti=[9, 1, 0]. Clamping.
2026-07-04 14:11:06,960 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=17.801 achieved=17.800761 (exact) bracket=[0.002, 68.406] s=0.260 variant=1 freq=15.0Hz max|I|=10.0A
2026-07-04 14:11:07,254 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=1 target_c=17.80 achieved=17.8008 err=0.0% B=0.07mT freq=15.0Hz [0.29s]
2026-07-04 14:11:07,260 [INFO] nhcs.collect - [ 1/10] concept=e357e1a5  b=[9,1,0]  novelty=0.608  freq=15.0Hz  BHI=0.917  CLI=0.099  SDR=0.2667  (6.9s)
2026-07-04 14:11:13,433 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:13,547 [INFO] nhcs.layer1_genesis.aian - AIAN kept 4/20 candidates.
2026-07-04 14:11:13,548 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 2/2 (2 unique signatures).
2026-07-04 14:11:13,564 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:13,582 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 47bbd0c1-ec54-45a2-b53c-c533b68ad8bd.
2026-07-04 14:11:13,582 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=26.235 achieved=26.235046 (exact) bracket=[0.002, 68.406] s=0.383 variant=2 freq=17.9Hz max|I|=10.0A
2026-07-04 14:11:13,802 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=2 target_c=26.24 achieved=26.2350 err=0.0% B=0.06mT freq=17.9Hz [0.22s] 
2026-07-04 14:11:13,806 [INFO] nhcs.collect - [ 2/10] concept=47bbd0c1  b=[6,2,0]  novelty=0.638  freq=17.9Hz  BHI=0.960  CLI=0.140  SDR=0.3076  (6.5s)
2026-07-04 14:11:20,465 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:20,511 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 14:11:20,511 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/4 (4 unique signatures).
2026-07-04 14:11:20,525 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:20,542 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 4c22329a-dd48-4154-a5fc-66735490419a.
2026-07-04 14:11:20,543 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 14:11:20,755 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.21s] 
2026-07-04 14:11:20,760 [INFO] nhcs.collect - [ 3/10] concept=4c22329a  b=[5,3,0]  novelty=0.603  freq=23.1Hz  BHI=0.974  CLI=0.152  SDR=0.0000  (7.0s)
2026-07-04 14:11:28,445 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:28,493 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 14:11:28,494 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5 (5 unique signatures).
2026-07-04 14:11:28,509 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:28,527 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 77896ff5-6f88-407f-ac29-8a57d07d2f26.
2026-07-04 14:11:28,527 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=36.778 achieved=36.777903 (exact) bracket=[5.149, 68.406] s=0.500 variant=4 freq=27.2Hz max|I|=10.0A
2026-07-04 14:11:28,745 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=4 target_c=36.78 achieved=36.7779 err=0.0% B=0.04mT freq=27.2Hz [0.22s]
2026-07-04 14:11:28,749 [INFO] nhcs.collect - [ 4/10] concept=77896ff5  b=[8,2,1]  novelty=0.619  freq=27.2Hz  BHI=0.976  CLI=0.149  SDR=0.0000  (8.0s)
2026-07-04 14:11:34,998 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:35,115 [INFO] nhcs.layer1_genesis.aian - AIAN kept 8/20 candidates.
2026-07-04 14:11:35,115 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/6 (6 unique signatures).
2026-07-04 14:11:35,141 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:35,152 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept edda74a9-71c6-4a7c-9704-0da65c39257b.
2026-07-04 14:11:35,152 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 14:11:35,372 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.22s]
2026-07-04 14:11:35,375 [INFO] nhcs.collect - [ 5/10] concept=edda74a9  b=[6,3,0]  novelty=0.624  freq=23.1Hz  BHI=0.979  CLI=0.154  SDR=0.0000  (6.6s)
2026-07-04 14:11:41,577 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:41,596 [INFO] nhcs.layer1_genesis.aian - AIAN kept 4/20 candidates.
2026-07-04 14:11:41,596 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch: pool collapsed to 1 unique signature (RSE produced no topological diversity this round).
2026-07-04 14:11:41,614 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:41,634 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept c78fa9f3-dfe9-4321-9236-cb85c70754a4.
2026-07-04 14:11:41,634 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=26.235 achieved=26.235046 (exact) bracket=[0.002, 68.406] s=0.383 variant=2 freq=17.9Hz max|I|=10.0A
2026-07-04 14:11:41,878 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=2 target_c=26.24 achieved=26.2350 err=0.0% B=0.06mT freq=17.9Hz [0.24s]
2026-07-04 14:11:41,881 [INFO] nhcs.collect - [ 6/10] concept=c78fa9f3  b=[6,2,0]  novelty=0.620  freq=17.9Hz  BHI=0.973  CLI=0.150  SDR=0.3092  (6.5s)
2026-07-04 14:11:48,447 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:48,514 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 14:11:48,514 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/4 (4 unique signatures).
2026-07-04 14:11:48,529 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:48,541 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 6b036e05-9617-4693-a534-85e57d175322.
2026-07-04 14:11:48,541 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=36.778 achieved=36.777903 (exact) bracket=[5.149, 68.406] s=0.500 variant=4 freq=27.2Hz max|I|=10.0A
2026-07-04 14:11:48,793 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=4 target_c=36.78 achieved=36.7779 err=0.0% B=0.04mT freq=27.2Hz [0.25s]
2026-07-04 14:11:48,797 [INFO] nhcs.collect - [ 7/10] concept=6b036e05  b=[6,4,0]  novelty=0.632  freq=27.2Hz  BHI=0.979  CLI=0.153  SDR=0.0000  (6.9s)
2026-07-04 14:11:55,239 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:11:55,272 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 14:11:55,273 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/4 (4 unique signatures).
2026-07-04 14:11:55,290 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:11:55,301 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept 6c989ea8-2665-499f-b7b0-abde4e67a13b.
2026-07-04 14:11:55,302 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=36.778 achieved=36.777903 (exact) bracket=[5.149, 68.406] s=0.500 variant=4 freq=27.2Hz max|I|=10.0A
2026-07-04 14:11:55,558 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=4 target_c=36.78 achieved=36.7779 err=0.0% B=0.04mT freq=27.2Hz [0.26s]
2026-07-04 14:11:55,562 [INFO] nhcs.collect - [ 8/10] concept=6c989ea8  b=[4,4,0]  novelty=0.608  freq=27.2Hz  BHI=0.978  CLI=0.165  SDR=0.0000  (6.8s)
2026-07-04 14:12:01,511 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:12:01,530 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 14:12:01,530 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/4 (4 unique signatures).
2026-07-04 14:12:01,548 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:12:01,559 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept e47ab7a8-308c-4d1e-bf74-387649f031af.
2026-07-04 14:12:01,560 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 14:12:01,835 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.27s]
2026-07-04 14:12:01,840 [INFO] nhcs.collect - [ 9/10] concept=e47ab7a8  b=[5,3,0]  novelty=0.612  freq=23.1Hz  BHI=0.978  CLI=0.159  SDR=0.0000  (6.3s)
2026-07-04 14:12:08,554 [INFO] nhcs.layer1_genesis.rse - RSE produced 20/20 valid candidates.
2026-07-04 14:12:08,559 [INFO] nhcs.layer1_genesis.aian - AIAN kept 5/20 candidates.
2026-07-04 14:12:08,560 [INFO] nhcs.layer1_genesis.search - DivergentBeamSearch selected 3/5 (5 unique signatures).
2026-07-04 14:12:08,574 [INFO] nhcs.layer1_genesis.icvp.consensus - Consensus: 5/5 approved (need 4) -> PASS
2026-07-04 14:12:08,598 [INFO] nhcs.layer1_genesis.icvp.ledger - Ledger committed concept c3952cdf-6186-444b-a490-964777cfacc8.
2026-07-04 14:12:08,599 [INFO] nhcs.layer2_tmft.controller - Controller(spectral): target_c=32.260 achieved=32.259536 (exact) bracket=[5.149, 68.406] s=0.429 variant=3 freq=23.1Hz max|I|=10.0A
2026-07-04 14:12:08,847 [INFO] nhcs.layer2_tmft.twin - DigitalTwin: I_f=3 target_c=32.26 achieved=32.2595 err=0.0% B=0.05mT freq=23.1Hz [0.25s]
2026-07-04 14:12:08,851 [INFO] nhcs.collect - [10/10] concept=c3952cdf  b=[6,3,0]  novelty=0.657  freq=23.1Hz  BHI=0.983  CLI=0.163  SDR=0.0000  (7.0s)
2026-07-04 14:12:08,852 [INFO] nhcs.collect -
2026-07-04 14:12:08,852 [INFO] nhcs.collect - === COLLECTION COMPLETE ===
2026-07-04 14:12:08,852 [INFO] nhcs.collect - Concepts collected : 10/10
2026-07-04 14:12:08,852 [INFO] nhcs.collect - Total attempts     : 10
2026-07-04 14:12:08,853 [INFO] nhcs.collect - Ledger size        : 42
2026-07-04 14:12:08,853 [INFO] nhcs.collect - Output             : data\nhcs_run_007.csv
2026-07-04 14:12:08,853 [INFO] nhcs.collect - ==================================================
2026-07-04 14:12:08,853 [INFO] nhcs.collect -
2026-07-04 14:12:08,854 [INFO] nhcs.collect - TOPOLOGY  beta1: 1-4 (mean 2.7)
2026-07-04 14:12:08,854 [INFO] nhcs.collect - NOVELTY   aggregate: 0.603-0.657 (mean 0.622)
2026-07-04 14:12:08,854 [INFO] nhcs.collect - SDR       range: 0.0000-0.3092 (mean 0.0883)
2026-07-04 14:12:08,854 [INFO] nhcs.collect - BHI       range: 0.917-0.983
2026-07-04 14:12:08,854 [INFO] nhcs.collect - CLI mean  range: 0.099-0.165
2026-07-04 14:12:08,854 [INFO] nhcs.collect -
2026-07-04 14:12:08,854 [INFO] nhcs.collect - PRIME1 distribution:
2026-07-04 14:12:08,854 [INFO] nhcs.collect -   HERE                   7/10
2026-07-04 14:12:08,855 [INFO] nhcs.collect -   BELOW                  2/10
2026-07-04 14:12:08,855 [INFO] nhcs.collect -   FAR                    1/10
```
