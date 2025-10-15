"""
Enhanced clustering module with optimization.

K-Means clustering with tolerance-based optimization to find local optima.
"""

from typing import List, Dict, Any, Tuple, Union, Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score


class Clusterer:
    """
    Enhanced K-Means clusterer with automatic optimization.
    
    Features:
    - Tolerance-based optimization (try k±tolerance)
    - Fixed count or ratio-based target
    - Category-aware clustering
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize clusterer.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state

    def cluster(
        self,
        embeddings: np.ndarray,
        n_clusters: int,
        normalize_embeddings: bool = True,
        calculate_quality: bool = True
    ) -> Tuple[np.ndarray, float]:
        """
        Cluster embeddings using K-Means.
        
        Args:
            embeddings: Array of shape (n_samples, embedding_dim)
            n_clusters: Number of clusters to create
            normalize_embeddings: L2-normalize before clustering
            calculate_quality: Calculate silhouette score
        
        Returns:
            Tuple of (cluster_labels, silhouette_score)
        """
        # Normalize embeddings if requested
        if normalize_embeddings:
            embeddings = normalize(embeddings, norm='l2')
        
        # Run K-Means
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Calculate quality metric
        sil_score = -1.0
        if calculate_quality and n_clusters > 1:
            try:
                sil_score = silhouette_score(embeddings, cluster_labels)
            except Exception as e:
                print(f"⚠️  Warning: Could not calculate silhouette score: {e}")
        
        return cluster_labels, sil_score

    def cluster_with_optimization(
        self,
        embeddings: np.ndarray,
        target: Union[int, float, str],
        tolerance: float = 0.2,
        test_points: int = 5,
        normalize_embeddings: bool = True,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Cluster with optimization - try multiple k values around target.
        
        Args:
            embeddings: Array of shape (n_samples, embedding_dim)
            target: Target clusters - int (fixed), float (ratio), or "200" / "0.05"
            tolerance: Tolerance as ratio (e.g., 0.2 = ±20%)
            test_points: Number of test points (should be odd for symmetry)
            normalize_embeddings: L2-normalize before clustering
            verbose: Print optimization progress
        
        Returns:
            Dict with:
                - best_k: Optimal cluster count
                - best_score: Best silhouette score
                - cluster_labels: Cluster assignments for best_k
                - tested_k_values: List of tested k values
                - scores: List of scores for each k
        """
        # Parse target to get base k
        if isinstance(target, str):
            if "." in target:
                # Ratio format "0.05"
                ratio = float(target)
                base_k = int(len(embeddings) * ratio)
            else:
                # Count format "200"
                base_k = int(target)
        elif isinstance(target, float):
            # Ratio
            base_k = int(len(embeddings) * target)
        else:
            # Fixed count
            base_k = target
        
        # Calculate k range
        k_range = int(base_k * tolerance)
        k_values = np.linspace(
            max(2, base_k - k_range),
            base_k + k_range,
            num=test_points,
            dtype=int
        )
        k_values = sorted(set(k_values))  # Remove duplicates, sort
        
        if verbose:
            print(f"Optimization: testing k values {list(k_values)}")
            print(f"  Target: {target}, Base k: {base_k}, Tolerance: ±{tolerance*100:.0f}%")
        
        # Test each k value
        best_k = base_k
        best_score = -1.0
        best_labels = None
        scores = []
        
        for k in k_values:
            if k >= len(embeddings):
                if verbose:
                    print(f"  k={k}: Skipped (more clusters than samples)")
                scores.append(-1.0)
                continue
            
            labels, score = self.cluster(
                embeddings=embeddings,
                n_clusters=k,
                normalize_embeddings=normalize_embeddings,
                calculate_quality=True
            )
            
            scores.append(score)
            
            if verbose:
                print(f"  k={k}: silhouette={score:.4f}")
            
            if score > best_score:
                best_score = score
                best_k = k
                best_labels = labels
        
        if verbose:
            print(f"✓ Best: k={best_k}, silhouette={best_score:.4f}")
        
        return {
            'best_k': best_k,
            'best_score': best_score,
            'cluster_labels': best_labels,
            'tested_k_values': list(k_values),
            'scores': scores
        }

    def cluster_by_category(
        self,
        embeddings: np.ndarray,
        categories: List[str],
        category_k_map: Dict[str, Union[int, str]],
        tolerance: float = 0.2,
        test_points: int = 5,
        normalize_embeddings: bool = True,
        optimize: bool = True,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Cluster separately by category with optional optimization.
        
        Args:
            embeddings: Array of shape (n_samples, embedding_dim)
            categories: List of category labels for each embedding
            category_k_map: Dict mapping category to target clusters
            tolerance: Tolerance for optimization
            test_points: Test points for optimization
            normalize_embeddings: L2-normalize before clustering
            optimize: Use optimization (if False, use exact k values)
            verbose: Print progress
        
        Returns:
            Dict with cluster assignments and scores per category
        """
        if len(embeddings) != len(categories):
            raise ValueError(f"embeddings ({len(embeddings)}) and categories ({len(categories)}) must match")
        
        # Group indices by category
        category_indices = {}
        for i, cat in enumerate(categories):
            if cat not in category_indices:
                category_indices[cat] = []
            category_indices[cat].append(i)
        
        # Initialize result arrays
        cluster_ids = [''] * len(embeddings)
        cluster_numbers = [-1] * len(embeddings)
        optimization_results = {}
        
        # Cluster each category separately
        for cat_name, indices in category_indices.items():
            if cat_name not in category_k_map:
                if verbose:
                    print(f"⚠️  Category '{cat_name}' not in category_k_map, skipping")
                continue
            
            target_k = category_k_map[cat_name]
            cat_embeddings = embeddings[indices]
            
            if verbose:
                print(f"\nCategory: {cat_name} ({len(cat_embeddings)} samples)")
            
            # Cluster with or without optimization
            if optimize:
                result = self.cluster_with_optimization(
                    embeddings=cat_embeddings,
                    target=target_k,
                    tolerance=tolerance,
                    test_points=test_points,
                    normalize_embeddings=normalize_embeddings,
                    verbose=verbose
                )
                labels = result['cluster_labels']
                optimization_results[cat_name] = result
            else:
                # Parse target_k
                if isinstance(target_k, str):
                    if "." in target_k:
                        k = int(len(cat_embeddings) * float(target_k))
                    else:
                        k = int(target_k)
                elif isinstance(target_k, float):
                    k = int(len(cat_embeddings) * target_k)
                else:
                    k = target_k
                
                labels, score = self.cluster(
                    embeddings=cat_embeddings,
                    n_clusters=k,
                    normalize_embeddings=normalize_embeddings,
                    calculate_quality=True
                )
                optimization_results[cat_name] = {'best_k': k, 'best_score': score}
            
            # Assign results back to original indices
            for i, label in zip(indices, labels):
                cluster_ids[i] = f"{cat_name}_{label}"
                cluster_numbers[i] = int(label)
        
        # Calculate cluster sizes
        cluster_sizes = {}
        for cid in cluster_ids:
            if cid:
                cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1
        
        return {
            'cluster_ids': cluster_ids,
            'cluster_numbers': cluster_numbers,
            'categories': categories,
            'optimization_results': optimization_results,
            'cluster_sizes': cluster_sizes,
            'total_clusters': len(cluster_sizes)
        }

    def get_cluster_statistics(self, cluster_labels: np.ndarray) -> Dict[str, Any]:
        """
        Calculate statistics for cluster assignments.
        
        Args:
            cluster_labels: Array of cluster assignments
        
        Returns:
            Dict with cluster statistics
        """
        unique_labels = np.unique(cluster_labels)
        cluster_counts = {}
        
        for label in unique_labels:
            cluster_counts[int(label)] = int(np.sum(cluster_labels == label))
        
        sizes = list(cluster_counts.values())
        
        return {
            'num_clusters': len(unique_labels),
            'cluster_sizes': cluster_counts,
            'min_size': min(sizes) if sizes else 0,
            'max_size': max(sizes) if sizes else 0,
            'mean_size': np.mean(sizes) if sizes else 0,
            'median_size': np.median(sizes) if sizes else 0
        }

