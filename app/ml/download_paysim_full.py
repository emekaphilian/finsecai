from pathlib import Path
import pandas as pd, requests
from tqdm import tqdm
import sys
paysim_path = Path("datasets/public_benchmark/paysim")
paysim_path.mkdir(parents=True, exist_ok=True)
paysim_file = paysim_path / "PS_20174392719_1491204439457_log.csv"
url = "https://raw.githubusercontent.com/EdgarLopezPhD/PaySim/master/PS_20174392719_1491204439457_log.csv"
print(f"Downloading FULL PaySim to {paysim_file}")
try:
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    with open(paysim_file, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True, desc="PaySim") as pbar:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
    print(f"\nDONE {paysim_file.stat().st_size / (1024**3):.2f} GB")
    df_check = pd.read_csv(paysim_file, usecols=['isFraud'])
    print(f"Rows: {len(df_check):,} Frauds: {df_check['isFraud'].sum():,}")
except Exception as e:
    print(f"Failed: {e}"); sys.exit(1)
