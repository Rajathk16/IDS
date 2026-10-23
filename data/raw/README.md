# CICIoT2023 Dataset Directory

This directory is designated for raw CSV files from the official **CICIoT2023** dataset provided by the Canadian Institute for Cybersecurity (University of New Brunswick).

Official Dataset URL:
https://www.unb.ca/cic/datasets/iotdataset-2023.html

## How to use:
1. Visit the link above and download one or more CSV partition files (e.g. `part-00000-363d1238-c2cd-4513-ae6e-39a0ab216f74-c000.csv` or any of the official subset CSVs).
2. Place the uncompressed `.csv` files into this directory: `data/raw/`.
3. Verify that the files are present by running:
   ```bash
   python src/cli.py audit --data-dir data/raw
   ```

## Note for Offline Development / Testing without real files:
If you do not have the real multi-gigabyte dataset downloaded yet, the system includes a synthetic generator that outputs realistic CICIoT2023-compatible schemas for testing:
```bash
python src/cli.py generate-synthetic --n-samples 2000 --output data/synthetic/synthetic_ciciot2023.csv
```
*Synthetic data is strictly labelled as synthetic in all reports, logs, and TUI screens.*
