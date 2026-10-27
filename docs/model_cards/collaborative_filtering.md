> **RETRACTED METRICS:** figures in this card came from a leaky/corrupted evaluation and are not valid. See README → *Verified status* and `ml/evaluation/results/verified_evaluation.json`.

# Model Card: Collaborative Filtering (ALS Matrix Factorization)

## Model Details
- **Model Name:** CollaborativeFilteringRecommender
- **Model Version:** 1.0.0
- **Model Type:** Matrix Factorization with Alternating Least Squares (ALS)
- **Framework:** PySpark ML (`pyspark.ml.recommendation.ALS`)
- **Latent Factors:** 50 latent dimensions
- **Regularization ($\lambda$):** 0.1
- **Max Iterations:** 15

## Intended Use
- **Primary Use:** Highly personalized hotel recommendations based on latent preference representations extracted from user-hotel rating matrices.
- **Matrix Sparsity Handled:** 99.999% sparse interaction space.

## Training Data
- **Training Interactions:** 43,812 ratings (80% temporal train split)
- **Entities:** 15,970 active reviewers, 50,780 hotels

## Evaluation Metrics (Held-Out Test Set, K=10)
- **NDCG@10:** 0.1696
- **Recall@10:** 0.1775
- **MAP:** 0.1671
- **Precision@10:** 0.0180

## Cold Start Behavior
- Users or items with zero historical ratings cannot be matched via matrix factorization alone. The system automatically routes new users to content-based or popularity modes.
