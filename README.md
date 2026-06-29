# HistoGeneAlign

**Multiscale Contrastive Alignment of H&E Histology and Spatial Transcriptomics**

HistoGeneAlign is a biomedical multimodal learning project that aligns **H&E histopathology image patches** with **spatial transcriptomics gene-expression profiles** at matched tissue locations.

The central question is:

> Can local H&E morphology retrieve the molecular gene-expression profile from the same spatial tissue region?

This is not a standard image-classification project. It is a **CLIP-style image-gene retrieval pipeline** for computational pathology and spatial biology.

---

## Why I Built This Project

H&E histology captures local tissue morphology:

```text
nuclei
cell density
glandular structure
stromal organization
tissue boundaries
extracellular matrix patterns
local tissue architecture
```

Spatial transcriptomics captures localized molecular state:

```text
gene-expression profiles
spatial biological programs
epithelial / stromal / immune activity
microenvironment variation
```

The hypothesis is:

> Local tissue morphology contains recoverable molecular information.

HistoGeneAlign tests this by learning a shared representation space where matched H&E patches and gene-expression profiles are close together, while unmatched pairs are farther apart.

---

## Project Architecture

```text
                 H&E Histology Patch
                         |
                         v
              Frozen Image Encoder
          Current: ResNet-50 baseline
          Future: UNI / CONCH encoders
                         |
                         v
              Image Projection Head
                         |
                         v
              Shared Contrastive Space
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

Training objective:

```text
Matched H&E patch + gene-expression profile     → close together
Unmatched H&E patch + gene-expression profile   → far apart
```

The model uses a **symmetric CLIP-style InfoNCE loss**:

```text
similarity = image_z @ gene_z.T / temperature
```

The diagonal entries are true image-gene pairs. Off-diagonal entries are contrastive negatives.

---

## Dataset

The current MVP uses the **TENX95** sample from the **HEST dataset**.

Relevant files:

```text
metadata/TENX95.json
st/TENX95.h5ad
patches/TENX95.h5
wsis/TENX95.tif
thumbnails/TENX95_downscaled_fullres.jpeg
spatial_plots/TENX95_spatial_plots.png
patches_vis/TENX95_patch_vis.jpg
pixel_size_vis/TENX95_pixel_size_vis.png
```

Important discovery:

```text
The coordinate and expression data are not separate CSV files.
They are stored inside st/TENX95.h5ad.
```

Important AnnData fields:

```text
adata.X                 → gene-expression matrix
adata.obs_names         → spot IDs
adata.var_names         → gene names
adata.obsm["spatial"]   → spatial coordinates
adata.obs               → per-spot metadata
adata.var               → per-gene metadata
```

---

## Data Summary

From `TENX95.h5ad`:

```text
Spatial spots: 11,845
Genes: 541
Expression matrix: 11,845 × 541
Sparsity: ~64.23%
```

From `patches/TENX95.h5`:

```text
Available H&E patches: 7,592
Patch image shape: 224 × 224 × 3
Patch barcode field available
Patch coordinate field available
```

The patch file contains fewer patches than the AnnData object has spots:

```text
AnnData spatial spots: 11,845
Available H&E patches: 7,592
Difference: 4,253 fewer patches than transcriptomic spots
```

So row-wise matching is invalid. The correct mapping is barcode-based:

```text
H5 barcode → spot_id → AnnData obs_names row
```

---

## Completed Workflow

```text
01_data_download_check.ipynb
        ↓
02_data_exploration.ipynb
        ↓
03_patch_extraction.ipynb
        ↓
04_embedding_extraction.ipynb
        ↓
05_contrastive_training.ipynb
        ↓
06_evaluation.ipynb
```

---

## What I Completed

### 1. Dataset Download and Validation

Verified that the TENX95 files are accessible and load correctly.

Confirmed:

```text
metadata/TENX95.json exists
st/TENX95.h5ad exists
patches/TENX95.h5 exists
wsis/TENX95.tif exists
safe preview images exist
AnnData object loads
spatial coordinates are available
gene-expression matrix is available
```

Key decisions:

```text
Use robust project-root detection.
Use exact HEST target-file downloads.
Do not preview the full-resolution WSI directly with PIL.
Use thumbnail and preview files for visualization.
```

---

### 2. Spatial Transcriptomics Exploration

Explored the TENX95 AnnData object and created a clean spot-level metadata table.

Confirmed:

```text
11,845 spatial spots
541 genes
spatial coordinates in adata.obsm["spatial"]
gene-expression matrix in adata.X
```

Created metadata fields:

```text
sample_id
spot_id
x
y
expression_available
coordinate_available
wsi_available
patch_h5_available
library_size
detected_genes
```

This table became the indexing layer for:

```text
spot_id → gene-expression row → patch index → image embedding row
```

Expression QC showed a valid but sparse spatial transcriptomics matrix. The MVP QC rule was:

```text
library_size >= 1000
detected_genes >= 100
```

Biological sanity-check markers included:

```text
GATA3, SERPINA3, CLIC6, ANKRD30A, LUM, MYBPC1,
TPD52, FLNB, POSTN, RUNX1, PGR, TACSTD2, ACTA2,
FOXA1, EPCAM, CXCL12, FASN, CCND1, DSP, KRT8
```

These genes suggest interpretable epithelial, stromal, extracellular matrix, immune, and microenvironment signals.

---

### 3. Patch Inspection and Image-Gene Alignment

Inspected `patches/TENX95.h5` and confirmed that the file already contains real H&E patches.

H5 structure:

```text
barcode | shape=(7592, 1)
coords  | shape=(7592, 2)
img     | shape=(7592, 224, 224, 3)
```

Mapping validation:

```text
Number of H5 patches: 7,592
Unique H5 spot IDs: 7,592
Duplicate H5 spot IDs: 0
Patch spot IDs found in AnnData-derived metadata: 7,592
Patch IDs missing from metadata: 0
Patch overlap fraction: 1.0
```

Created aligned image-gene table:

```text
data/processed/TENX95_aligned_image_gene_table.csv
```

Aligned table result:

```text
Rows: 7,592
Missing values: 0
Valid patch rows: 7,592
Valid expression rows: 7,592
Rows passing MVP QC: ~7,530
```

---

### 4. Frozen Image Embedding Extraction

Used a frozen **ResNet-50 ImageNet encoder** to convert H&E patches into image embeddings.

Image pipeline:

```text
H&E patch
→ uint8 RGB image
→ float tensor
→ ImageNet normalization
→ frozen ResNet-50
→ 2,048-dimensional embedding
```

Outputs:

```text
data/embeddings/TENX95_resnet50_image_embeddings.npy
data/embeddings/TENX95_resnet50_image_embedding_metadata_full.csv

data/embeddings/TENX95_resnet50_image_embeddings_qc.npy
data/embeddings/TENX95_resnet50_image_embedding_metadata_qc.csv
```

Shapes:

```text
Full image embeddings: (7592, 2048)
QC image embeddings:   (7530, 2048)
```

Alignment validation passed:

```text
7530 / 7530 QC rows matched between metadata spot_id and AnnData obs_names.
```

---

### 5. Contrastive Training

Trained the first HistoGeneAlign contrastive baseline.

Model setup:

```text
Image branch:
2048-dimensional frozen ResNet-50 embedding
→ trainable image projection head
→ 256-dimensional shared latent

Gene branch:
541-dimensional processed gene vector
→ MLP gene encoder
→ gene projection head
→ 256-dimensional shared latent
```

Gene preprocessing:

```text
raw counts
→ library-size normalization to 10,000
→ log1p transform
→ StandardScaler fitted on train split only
```

Training setup:

```text
Split: random spot split
Train / validation / test: 70% / 15% / 15%
Batch size: 64
Epochs: 20
Learning rate: 1e-4
Optimizer: AdamW
Temperature: 0.07
Projection dimension: 256
Hidden dimension: 512
Dropout: 0.10
Seed: 42
```

Saved outputs:

```text
outputs/checkpoints/TENX95_resnet50_contrastive_baseline.pt
outputs/metrics/TENX95_contrastive_training_history.csv
outputs/metrics/TENX95_contrastive_final_test_metrics.json

data/embeddings/TENX95_resnet50_contrastive_image_latents_qc.npy
data/embeddings/TENX95_resnet50_contrastive_gene_latents_qc.npy
data/embeddings/TENX95_contrastive_qc_metadata_with_splits.csv
```

Saved latent shapes:

```text
Image latents: (7530, 256)
Gene latents:  (7530, 256)
```

---

### 6. Retrieval Evaluation

Evaluated bidirectional retrieval in the learned contrastive latent space.

Evaluation directions:

```text
Image → Gene retrieval
Gene → Image retrieval
```

Metrics:

```text
Recall@1
Recall@5
Recall@10
Recall@50
Median Rank
Mean Rank
MRR
```

Test set size:

```text
N_test = 1130
```

Random baseline:

```text
Random Recall@1  ≈ 1 / 1130  ≈ 0.000885
Random Recall@5  ≈ 5 / 1130  ≈ 0.004425
Random Recall@10 ≈ 10 / 1130 ≈ 0.008850
```

Main test results:

| Direction | Recall@1 | Recall@5 | Recall@10 | Median Rank | MRR |
|---|---:|---:|---:|---:|---:|
| Image → Gene | 0.08584 | 0.29292 | 0.41504 | 17 / 1130 | 0.1901 |
| Gene → Image | 0.08584 | 0.27434 | 0.38407 | 17 / 1130 | 0.1860 |

Interpretation:

```text
Image → Gene Recall@1 is ~97× random.
Image → Gene Recall@10 is ~47× random.
Median rank is 17 out of 1130 candidates.
```

For half of the test spots, the true match is ranked within the top 17 candidates, approximately the top 1.5% of the test candidate set.

Similarity matrix summary:

```text
Diagonal mean similarity:      0.3639
Off-diagonal mean similarity:  0.0566
Diagonal advantage:            0.3073
```

This indicates that matched H&E image-gene pairs are substantially closer than mismatched pairs in the learned latent space.

---

## Current Result Summary

The first ResNet-50 contrastive baseline demonstrates clear above-random spot-level retrieval between H&E morphology and spatial transcriptomics profiles on TENX95.

Fair claim:

> HistoGeneAlign learns a meaningful morphology-transcriptomics alignment at the spot level on TENX95, achieving Image→Gene Recall@10 of ~41.5%, Gene→Image Recall@10 of ~38.4%, and a median retrieval rank of 17 out of 1130 test candidates.

---

## Current Status

### Completed

```text
Dataset download and validation
AnnData loading
Spatial coordinate extraction
Expression matrix inspection
Spot metadata table creation
Gene-expression QC
Biological marker interpretation
H&E thumbnail overlay
Patch H5 inspection
Barcode-based patch-to-spot mapping
Aligned image-gene table creation
Frozen ResNet-50 image embedding extraction
Image embedding QC
Contrastive model training
Bidirectional image-gene retrieval evaluation
Similarity matrix analysis
Rank distribution analysis
Spatial top-1 success visualization
PCA visualization of shared latent space
Retrieval patch example visualization
```

### Current Model

```text
Image encoder: frozen ResNet-50 ImageNet baseline
Image embedding dimension: 2048
Gene input dimension: 541
Shared latent dimension: 256
Training split: random spot split
Dataset sample: TENX95
```

---

## Limitations

The current result is promising but early.

Do not claim yet that the model generalizes across patients, slides, tissue types, or datasets.

Current limitations:

```text
The model has been tested on one HEST sample: TENX95.
The current evaluation uses a random spot split.
Random spot splits may benefit from spatial autocorrelation.
Nearby tissue regions can share morphology and gene expression.
The image encoder is generic ImageNet ResNet-50, not pathology-specific.
The train/test gap suggests overfitting or memorization pressure.
No cross-slide or cross-patient generalization has been tested yet.
No UNI or CONCH comparison has been run yet.
No cell-type composition branch has been implemented yet.
```

Observed train/test gap:

```text
Train mean Recall@1:      ~0.9445
Validation mean Recall@1: ~0.0939
Test mean Recall@1:       ~0.0858
```

The model strongly fits training pairs but still generalizes above random to held-out test spots. The next evaluation should test spatial generalization more strictly.

---

## Immediate Future Step

### Spatial Block Split Evaluation

The next serious experiment is a spatial block split.

Reason:

```text
Random spot splitting can overestimate performance because nearby spots may appear in both train and test sets.
Spatial block splitting holds out entire tissue regions.
```

Main question:

> Can the model retrieve image-gene pairs from spatial regions it did not train on?

Planned notebook:

```text
07_spatial_block_split_experiment.ipynb
```

Expected comparison:

```text
Random split baseline:
Image → Gene Recall@10 ≈ 41.5%
Gene → Image Recall@10 ≈ 38.4%
Median rank ≈ 17 / 1130

Spatial block split:
Expected to be lower.
If still above random, the evidence becomes much stronger.
```

---

## Next Modeling Improvements

After the spatial split experiment:

### 1. Compare pathology foundation encoders

```text
ResNet-50 baseline
UNI
CONCH
```

### 2. Improve gene-side representation

```text
gene variance filtering
PCA + MLP
pathway or gene-set features
stronger normalization checks
```

### 3. Add stronger evaluation

```text
paired distance vs random distance
spatial retrieval distance analysis
expression similarity of wrong retrieved spots
qualitative retrieval examples by success/failure
cross-slide or cross-sample testing
```

### 4. Add biological cell-composition branch

Possible extension:

```text
Spatial transcriptomics expression
→ marker-gene scoring or deconvolution
→ cell-type composition vector per spot

H&E patch or subpatch features
→ feature aggregation
→ prediction head
→ predicted cell-type composition
```

Recommended starting point:

```text
Use marker-gene scores first.
Do not start with full cell2location immediately.
```

---

## Repository Structure

```text
HistoGeneAlign-Multiscale-H-E-Spatial-Transcriptomics-Contrastive-Learning/
│
├── notebooks/
│   ├── 01_data_download_check.ipynb
│   ├── 02_data_exploration.ipynb
│   ├── 03_patch_extraction.ipynb
│   ├── 04_embedding_extraction.ipynb
│   ├── 05_contrastive_training.ipynb
│   └── 06_evaluation.ipynb
│
├── outputs/
│   ├── figures/
│   ├── metrics/
│   └── checkpoints/
│
├── reports/
├── scripts/
├── src/
├── config.yaml
├── environment.yml
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

Large data artifacts are intentionally excluded from GitHub:

```text
data/raw/
data/processed/
data/patches/
data/embeddings/
outputs/checkpoints/
outputs/logs/
*.pt
*.pth
*.ckpt
*.h5ad
*.h5
*.svs
*.tif
*.tiff
```

---

## Tech Stack

```text
Python
CUDA
PyTorch
Torchvision
Scanpy
AnnData
NumPy
Pandas
Scikit-learn
H5Py
Matplotlib
```

---

## Current Status in One Line

HistoGeneAlign has completed the first full MVP loop: **data validation → image-gene alignment → ResNet-50 embedding extraction → contrastive training → bidirectional retrieval evaluation**, with strong above-random retrieval on TENX95 and spatial block evaluation planned next.
