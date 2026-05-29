# HistoGeneAlign

## Why I Did This Project

HistoGeneAlign is a biomedical multimodal learning project that connects **H&E histopathology images** with **spatial transcriptomics gene-expression profiles**.

The main idea is:

> Can the visual structure of tissue in an H&E image help retrieve or predict the molecular gene-expression state of the same tissue region?

This project was built to explore how **computer vision, spatial biology, and contrastive learning** can be combined for spot-level image–gene alignment.

---

## Project Architecture

```text
Spatial Transcriptomics (.h5ad)
        |
        |--> Spot IDs
        |--> X/Y spatial coordinates
        |--> Gene-expression matrix
        |
        v
Gene Branch
Gene expression → preprocessing → gene encoder → shared embedding space


H&E Histology Patches (.h5)
        |
        |--> Patch inspection
        |--> Patch quality check
        |--> Frozen ResNet-50 embedding extraction
        |
        v
Image Branch
H&E patch → ResNet-50 encoder → image embedding → shared embedding space


Final Goal:
Matched H&E patch and gene-expression profile should be close together.
Unmatched pairs should be far apart.
```

The planned model uses a **CLIP-style contrastive learning objective**, where each image patch is aligned with its corresponding spatial transcriptomics profile.

---

## What I Did Till Now

### 1. Dataset Download and Validation

I started with the **TENX95 sample from the HEST dataset**.

I verified that the required files are available:

```text
metadata/TENX95.json
st/TENX95.h5ad
patches/TENX95.h5
wsis/TENX95.tif
thumbnails/TENX95_downscaled_fullres.jpeg
```

A key discovery was that the coordinate and expression data are not stored as separate CSV files. They are stored inside:

```text
st/TENX95.h5ad
```

Inside this file:

```text
adata.X                 → gene-expression matrix
adata.obs_names         → spot IDs
adata.var_names         → gene names
adata.obsm["spatial"]   → spatial coordinates
```

---

### 2. Spatial Transcriptomics Exploration

I explored the AnnData object and confirmed:

```text
11,845 spatial spots
541 genes
Spatial coordinates available
Gene-expression matrix available
```

I also created a clean spot-level metadata table containing:

```text
sample_id
spot_id
x coordinate
y coordinate
expression availability
coordinate availability
WSI availability
patch file availability
```

This table becomes the backbone for linking gene-expression data with H&E image patches.

---

### 3. Expression Matrix Quality Check

I checked the gene-expression matrix and found that it is sparse, which is expected in spatial transcriptomics.

Important observations:

```text
Matrix shape: 11,845 × 541
Sparsity: ~64%
Many spots have low or near-zero expression
Some spots show strong molecular signal
```

This means the gene branch will need preprocessing before modeling:

```text
library-size normalization
log1p transformation
highly variable gene selection
optional scaling
```

---

### 4. Biological Sanity Check

I inspected highly expressed genes and found biologically meaningful markers related to:

```text
epithelial identity
stromal structure
extracellular matrix
smooth muscle / myofibroblast-like signal
immune or microenvironment activity
```

This confirmed that the expression matrix contains real biological signal rather than random noise.

---

### 5. Spatial Coordinate Visualization

I plotted the spatial coordinates and overlaid them on the H&E thumbnail.

This confirmed that the spatial transcriptomics grid aligns with the tissue image, which is essential for image–gene pairing.

---

### 6. H&E Patch Inspection

I inspected the existing patch file:

```text
patches/TENX95.h5
```

The file contains real H&E image patches with visible morphology, including:

```text
cellular regions
stromal regions
fibrous tissue
background / tissue-edge patches
```

I also found an important mismatch:

```text
AnnData spots: 11,845
Available patches: 7,592
```

So the project cannot assume row-wise matching between spots and patches. The patch-to-spot mapping still needs to be resolved.

---

### 7. Image Embedding Extraction

I used a frozen **ResNet-50 encoder** to convert H&E patches into image embeddings.

Current image pipeline:

```text
H&E patch
→ resize to 224 × 224
→ normalize image channels
→ frozen ResNet-50
→ 2,048-dimensional image embedding
```

The embedding quality check showed stable embedding norms, meaning the image branch is working correctly.

---

## Current Project Status

### Completed

```text
Dataset download
AnnData loading
Spatial coordinate extraction
Expression matrix inspection
Spot metadata table creation
Gene-expression QC
Biological marker interpretation
H&E thumbnail overlay
Patch H5 inspection
Patch count validation
Frozen ResNet-50 image embedding extraction
Embedding quality check
```

### Current Bottleneck

```text
Patch-to-spot mapping
```

The next major task is to correctly align:

```text
spot_id ↔ patch_index ↔ gene-expression vector ↔ image embedding
```

---

## Next Steps

### 1. Resolve Patch-to-Spot Mapping

Build a clean aligned table:

```text
spot_id
patch_index
gene_expression_row
image_embedding_row
x coordinate
y coordinate
```

This is required before contrastive training.

---

### 2. Preprocess Gene Expression

Apply:

```text
library-size normalization
log1p transformation
highly variable gene selection
scaling
```

This will prepare the gene vectors for the gene encoder.

---

### 3. Build PyTorch Dataset

Create a dataset that returns matched image–gene pairs:

```python
{
    "spot_id": spot_id,
    "image_embedding": image_embedding,
    "gene_expression": expression_vector
}
```

---

### 4. Build the Gene Encoder

Use a simple MLP to convert gene-expression vectors into embeddings.

Planned structure:

```text
gene expression vector
→ MLP encoder
→ projection head
→ normalized gene embedding
```

---

### 5. Train Contrastive Model

Train using symmetric image-to-gene and gene-to-image contrastive loss.

Goal:

```text
matched image–gene pairs close together
unmatched pairs far apart
```

---

### 6. Evaluate Retrieval

Evaluate both directions:

```text
Image → Gene retrieval
Gene → Image retrieval
```

Metrics:

```text
Recall@1
Recall@5
Recall@10
Median Rank
MRR
```

---

### 7. Improve Image Encoder Later

The current **ResNet-50 encoder** is a baseline. Later, compare it with pathology-specific encoders such as:

```text
UNI
CONCH
```

---
