# 📥 Dataset Acquisition — Step-by-Step

The pipeline expects **two** files at `ml/data/raw/`:

| File | Required | Source |
|------|---------|--------|
| `diabetic_data.csv` | Yes | Kaggle → UCI Diabetes |
| `IDS_mapping.csv` | Yes | Same zip |

The script `python ml/data/download_dataset.py` will:
1. Try the Kaggle CLI if `~/.kaggle/kaggle.json` exists
2. Try incoming files at `ml/data/raw/incoming/`
3. Try the public UCI mirror
4. Fall back to a synthetic CSV (so you can run today, then swap real data later)

---

## ✅ Easiest path — Kaggle (manual, 1 minute)

1. Open the dataset page: <https://www.kaggle.com/datasets/brandao/diabetes>
2. Click **Download** (top-right, blue button). You may need to sign in first — sign-in is free.
3. You'll get a ~28 MB zip named `diabetes.zip`.
4. Unzip **inside the project** so the files land in `ml/data/raw/incoming/`:
   ```
   ml/data/raw/incoming/diabetic_data.csv
   ml/data/raw/incoming/IDS_mapping.csv
   ```
5. Run:
   ```bash
   python ml/data/download_dataset.py
   ```

---

## ✅ Canonical path — Kaggle CLI (automatic, 5 minutes)

1. Sign in to <https://www.kaggle.com/> → **Avatar → Settings → Create New Token**.
2. Place the downloaded `kaggle.json` at:
   - **Windows:** `C:\Users\<you>\.kaggle\kaggle.json`
   - **Mac/Linux:** `~/.kaggle/kaggle.json`
3. `pip install kaggle`
4. From the project root:
   ```bash
   python ml/data/download_dataset.py
   ```

Direct downloads are mandatory under the dataset's CC0 license. The download script verifies the file sizes before extracting.

---

## ✅ Backup — UCI mirror

The dataset is also published by the **UCI Machine Learning Repository**:

* <https://archive.ics.uci.edu/dataset/296/diabetes>
* <https://archive.ics.uci.edu/ml/machine-learning-databases/00296/>

`download_dataset.py` will automatically try the UCI mirror if Kaggle fails.

---

## ✅ Sanity test — synthetic CSV (no credentials needed)

If you want to **validate the entire pipeline today** without any download:

```bash
python ml/data/download_dataset.py --force-synthetic
```

This generates a structurally similar CSV locally using `make_synthetic_diabetes.py`. **DO NOT use it for clinical decisions.** After you have Kaggle creds, run the script again without `--force-synthetic` to upgrade.

---

## ✅ Where the files live after download

```
lifeguard-readmission/
└── ml/
    └── data/
        └── raw/
            ├── diabetic_data.csv          ← ML script input
            ├── IDS_mapping.csv           ← ID lookups (admission/discharge/source)
            └── incoming/                   ← files you drop here manually
```

After this, run:

```bash
dvc repro     # prepare → split → features → train → evaluate
```

Expected runtime: ~30 seconds on a laptop for the synthetic dataset, 1–2 minutes for the real Kaggle data (~100k rows).

---

## ✅ Recommended datasets beyond Kaggle

Once you're comfortable with the pipeline, expand coverage with free public datasets to de-bias the model:

| Dataset | How to get it | Why |
|---------|---------------|-----|
| **UCI Diabetes 130** (used today) | already wired in | baseline |
| **MIMIC-IV** | Apply at <https://physionet.org/content/mimiciv/2.2/> (CITI course ~2 h) | gold-standard ICU cohort |
| **CMS DE-SynPUF** | Pull from <https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs> | national Medicare incidence | 
| **Synthea** | `pip install synthea`; `synthea -p 1000` | unlimited FHIR-format synthetic data |
| **eICU** | Apply at <https://physionet.org/content/eicu-crd/> | multi-center ICU telemetry |

Each one plugs into the same `ml/data/prepare_*.py` style.

---

## 🛟 If something is wrong

* **`Kaggle.json not found`** — confirm the file is at the path above; on Windows also run `set KAGGLE_USERNAME=...` and `set KAGGLE_KEY=...`
* **`403 Token not expired`** — generate a new API token (old ones expire)
* **`SSL error on UCI mirror`** — try a VPN, or manually drop the CSVs into `ml/data/raw/incoming/`
* **Still stuck?** — run `python ml/data/download_dataset.py --force-synthetic` to keep moving; the rest of the pipeline doesn't care which source produced the CSV.
