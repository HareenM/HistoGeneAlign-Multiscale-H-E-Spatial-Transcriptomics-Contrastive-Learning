# HistoGeneAlign

**Contrastive Alignment of H&E Histology and Spatial Transcriptomics**

HistoGeneAlign aligns H&E histopathology image patches with spatial transcriptomics gene-expression profiles from the same tissue locations. It uses a CLIP-style contrastive objective and evaluates with spot-level retrieval.

The question it tests:

> Can local H&E morphology retrieve the gene-expression profile of the same spatial spot?

> **Note on the repository name.** The repo is named `...-Multiscale-...`, but the current implementation is single-scale. One 224x224 patch produces one global ResNet-50 embedding. Multiscale patch aggregation is a planned extension that has not been built. See "What this is not yet."

---

## Status at a glance

| Item | State |
|---|---|
| End-to-end pipeline (data to embeddings to training to retrieval) | Runs on one sample |
| Sample used | TENX95 (HEST-1k), single slide |
| Image encoder | Frozen ImageNet ResNet-50 (HEST-1k weak baseline) |
| Method novelty | None yet. BLEEP-style pipeline, reimplemented |
| Headline retrieval number | Random spot split only, leakage-susceptible |
| Generalization tested | No. Spatial block split is the pending gate |

Read the results section with the leakage caveat in mind. The top-line Recall@10 is very likely inflated by spatial autocorrelation between neighboring spots. Treat it as an upper bound until the block-split experiment is run.

---

## What this is not yet

Stated plainly so the numbers below are not misread:

- **Not multiscale.** Single 224x224 patch, single global embedding. No multi-resolution input and no subpatch aggregation.
- **Not a new method.** The design (frozen image encoder, gene MLP, symmetric InfoNCE, spot-level retrieval) is the same core recipe as BLEEP (Xie et al., NeurIPS 2023). This repo is an independent implementation of that recipe on one HEST-1k sample.
- **Not pathology-pretrained.** The encoder is ImageNet ResNet-50, which is the weak baseline from the HEST-1k benchmark (Jaume et al., 2024). It is not UNI, CONCH, or Virchow2.
- **Not validated for generalization.** Every reported number comes from a random spot split on a single slide. No cross-region, cross-slide, or cross-patient evaluation has been run.

---

## Relationship to prior work

This is an implementation-and-diagnosis exercise, not a novel model.

- **BLEEP (Xie et al., NeurIPS 2023)** introduced bimodal contrastive alignment of H&E patches and spot expression for retrieval and reference-based expression prediction. HistoGeneAlign reproduces that alignment recipe.
- **HEST-1k (Jaume et al., 2024)** supplies the TENX95 sample and standard baselines. The frozen ResNet-50 used here corresponds to the benchmark's weak encoder.

What the repository currently adds is engineering (a clean, barcode-correct data pipeline on TENX95) and an in-progress leakage characterization. It does not yet add a method.

---

## Why the project exists

H&E histology captures local tissue morphology: nuclei, cell density, glandular structure, stromal organization, tissue boundaries, extracellular matrix. Spatial transcriptomics captures localized molecular state: per-spot gene-expression profiles reflecting epithelial, stromal, and immune activity.

The working hypothesis is that local morphology carries recoverable information about local molecular state. HistoGeneAlign tests it by learning a shared space where a matched patch and its gene profile sit close together and mismatched pairs sit farther apart, then measuring how often the true match can be retrieved.

Whether this hypothesis holds is exactly what the current evaluation cannot yet answer, because the random split does not separate genuine morphology-to-expression signal from leakage between adjacent spots.

---

## Architecture

```text
                 H&E Histology Patch
                         |
                         v
              Frozen Image Encoder
          Current: ResNet-50 (ImageNet)
          Future:  UNI / CONCH / Virchow2
                         |
                         v
              Image Projection Head
                         |
                         v
              Shared Contrastive Space (256-d)
                         ^
                         |
                Gene Projection Head
                         ^
                         |
                  Gene Encoder MLP
                         ^
                         |
        Spatial Transcriptomics Gene Profile
```

Objective: symmetric CLIP-style InfoNCE.

```text
similarity = image_z @ gene_z.T / temperature
```

Diagonal entries are true image-gene pairs. Off-diagonal entries are contrastive negatives.

---

## Dataset

The current run uses the **TENX95** sample from **HEST-1k**.

Files:

```text
metadata/TENX95.json
st/TENX95.h5ad
patches/TENX95.h5
wsis/TENX95.tif
thumbnails/TENX95_downscaled_fullres.jpeg
spatial_plots/TENX95_spatial_plots.png
```

Coordinate and expression data are not separate CSVs. They live inside `st/TENX95.h5ad`:

```text
adata.X                 -> gene-expression matrix
adata.obs_names         -> spot IDs
adata.var_names         -> gene names
adata.obsm["spatial"]   -> spatial coordinates
adata.obs               -> per-spot metadata
adata.var               -> per-gene metadata
```

### Data summary

From `TENX95.h5ad`:

```text
Spatial spots:      11,845
Genes:              541
Expression matrix:  11,845 x 541
Sparsity:           ~64.2%
```

From `patches/TENX95.h5`:

```text
H&E patches:        7,592
Patch shape:        224 x 224 x 3
Barcode and coordinate fields present
```

The patch file has fewer patches than the AnnData object has spots (7,592 vs 11,845), so row-wise matching is invalid. Mapping is barcode-based:

```text
H5 barcode -> spot_id -> AnnData obs_names row
```

---

## What is actually done

Engineering completed and verified on TENX95:

```text
Dataset download and file validation
AnnData loading and spatial-coordinate extraction
Spot-level metadata table
Gene-expression QC (library_size >= 1000, detected_genes >= 100)
Barcode-based patch-to-spot mapping (7,592/7,592 matched, 0 missing)
Aligned image-gene table (7,592 rows, ~7,530 passing QC)
Frozen ResNet-50 embedding extraction (7,530 QC patches, 2048-d)
Contrastive training (one run)
Bidirectional retrieval evaluation and similarity analysis
```

Notebook flow:

```text
01_data_download_check -> 02_data_exploration -> 03_patch_extraction
-> 04_embedding_extraction -> 05_contrastive_training -> 06_evaluation
```

### Model and training setup

```text
Image branch: 2048-d frozen ResNet-50 -> projection head -> 256-d
Gene branch:  541-d gene vector -> MLP -> projection head -> 256-d

Gene preprocessing:
  raw counts -> library-size norm to 10,000 -> log1p
  -> StandardScaler fit on train split only

Split:        random spot split, 70/15/15
Batch size:   64
Epochs:       20
LR:           1e-4 (AdamW)
Temperature:  0.07
Latent dim:   256
Hidden dim:   512
Dropout:      0.10
Seed:         42
```

---

## Results (random spot split, single slide)

These numbers describe one training run under a random spot split on TENX95. See the leakage section immediately after before drawing any conclusion.

Test set: N = 1,130. Random Recall@1 ≈ 0.00088, Recall@10 ≈ 0.0088.

| Direction | Recall@1 | Recall@5 | Recall@10 | Median Rank | MRR |
|---|---:|---:|---:|---:|---:|
| Image -> Gene | 0.0858 | 0.2929 | 0.4150 | 17 / 1130 | 0.190 |
| Gene -> Image | 0.0858 | 0.2743 | 0.3841 | 17 / 1130 | 0.186 |

Similarity structure:

```text
Diagonal (matched) mean:     0.3639
Off-diagonal (mismatched):   0.0566
Separation:                  0.3073
```

Matched pairs sit closer than mismatched pairs in the learned space. Whether that separation reflects biology or leakage is unresolved (next section).

---

## The leakage problem (read before trusting the numbers)

The train-versus-held-out gap is large:

```text
Train mean Recall@1:       ~0.9445
Validation mean Recall@1:  ~0.0939
Test mean Recall@1:        ~0.0858
```

Two things are happening, and the current design cannot separate them:

1. **Memorization.** With a frozen encoder and trainable projection heads, each near-unique gene vector can be mapped close to its own image embedding on the training set. Train Recall@1 of 0.94 is consistent with the heads fitting individual training pairs rather than learning transferable structure.

2. **Spatial autocorrelation under random splitting.** Visium spots are physically close and their neighbors are highly correlated in both morphology and expression. A random split scatters adjacent spots across train and test. A test spot can then be "retrieved" partly because a near-identical neighbor was in training. This inflates held-out retrieval above random without requiring any genuine morphology-to-expression mapping.

Because of point 2, the Recall@10 of 0.415 should be read as a leakage-susceptible upper bound, not evidence that morphology predicts expression. The honest position is that the amount of real signal, if any, is unknown until the spatial block split is run.

Ratios such as "N times random" are not reported as achievements here, because a number that is contaminated by leakage does not become meaningful by dividing it by the random rate.

---

## Honest claim (current)

What can be said now, without overstating:

> On a single HEST-1k slide (TENX95), a BLEEP-style contrastive model with a frozen ImageNet ResNet-50 encoder, trained and evaluated under a random spot split, retrieves the correct gene profile within the top 10 for about 41% of held-out spots. Given a train Recall@1 of 0.94 and the spatial autocorrelation of Visium data, this figure is likely inflated by leakage between adjacent spots. No claim of generalization across regions, slides, patients, or tissue types is supported by the current evidence.

---

## Limitations

```text
Tested on one HEST-1k sample (TENX95) only.
Evaluation uses a random spot split, which is leakage-susceptible.
The image encoder is generic ImageNet ResNet-50, not pathology-specific.
The large train/test gap indicates memorization, poor generalization, or both.
No spatial block, cross-slide, or cross-patient evaluation has been run.
No UNI / CONCH / Virchow2 comparison exists yet.
No cell-type composition branch is implemented.
The gene set (541 genes) and single-scale patching are unoptimized.
```

---

## Immediate next step: spatial block split (the gate)

This is the experiment that determines whether the project has a real result or a leakage artifact.

```text
Random spot split can overestimate performance because adjacent spots
appear in both train and test. A spatial block split holds out entire
contiguous tissue regions, so test spots have no training neighbors.
```

Question:

> Can the model retrieve image-gene pairs from tissue regions it never trained on?

Planned notebook: `07_spatial_block_split_experiment.ipynb`

Expected outcome:

```text
Random split:       Image->Gene Recall@10 ~ 0.415
Spatial block split: expected to drop, possibly toward random.
If it stays meaningfully above random, the evidence becomes real.
If it collapses to random, the current numbers were leakage.
```

Until this is run, the random-split results should not appear as a headline in any portfolio, application, or conversation.

---

## Roadmap after the block split

Ordered by evidentiary value, not effort:

1. **Leakage characterization as the deliverable.** Report random split, spatial block split, and cross-slide split side by side, with PCC and R2 on expression alongside retrieval metrics. This is the most defensible framing for a workshop or short paper: an honest measurement of how much apparent performance is leakage under standard splitting.
2. **Pathology encoders.** Swap ResNet-50 for UNI, CONCH, and Virchow2 and re-measure under all splits. This tests whether a stronger encoder survives the block split where the weak baseline may not.
3. **Gene-side representation.** Variance filtering, PCA plus MLP, and gene-set or pathway features, with normalization checks.
4. **Cell-composition branch (later).** Marker-gene scoring first, deconvolution (for example cell2location) only if warranted.

---

## Repository structure

```text
HistoGeneAlign-.../
|
|-- notebooks/
|   |-- 01_data_download_check.ipynb
|   |-- 02_data_exploration.ipynb
|   |-- 03_patch_extraction.ipynb
|   |-- 04_embedding_extraction.ipynb
|   |-- 05_contrastive_training.ipynb
|   `-- 06_evaluation.ipynb
|
|-- outputs/            (figures, metrics, checkpoints)
|-- reports/
|-- scripts/
|-- src/
|-- config.yaml
|-- environment.yml
|-- requirements.txt
|-- README.md
|-- LICENSE
`-- .gitignore
```

Large artifacts are excluded from version control (`data/`, `*.pt`, `*.h5ad`, `*.h5`, `*.tif`, checkpoints, logs).

---

## Tech stack

```text
Python, PyTorch, Torchvision, CUDA
Scanpy, AnnData, H5Py
NumPy, Pandas, Scikit-learn, Matplotlib
```

---

## Status in one line

HistoGeneAlign runs a complete BLEEP-style pipeline (data validation, barcode-correct alignment, frozen ResNet-50 embeddings, contrastive training, bidirectional retrieval) on one HEST-1k slide. The random-split retrieval numbers are leakage-susceptible and unverified for generalization. The spatial block split is the next experiment and the gate for any real claim.
