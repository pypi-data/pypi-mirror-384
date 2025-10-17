import numpy as np
from sklearn.ensemble import RandomForestClassifier

from nonconform.estimation.weight.base import BaseWeightEstimator


class ForestWeightEstimator(BaseWeightEstimator):
    """Random Forest-based weight estimator for covariate shift.

    Uses Random Forest classifier to estimate density ratios between calibration
    and test distributions. Random Forest can capture non-linear relationships
    and complex interactions between features, making it suitable for handling
    more complex covariate shift patterns than logistic regression.

    The Random Forest is trained to distinguish between calibration and test samples,
    and the predicted probabilities are used to compute importance weights
    w(x) = p_test(x) / p_calib(x).

    Args:
        n_estimators (int): Number of trees in the forest. Defaults to 100.
        max_depth (int, optional): Maximum depth of trees. If None, nodes are
            expanded until all leaves are pure. Defaults to 5 to prevent overfitting.
        min_samples_leaf (int): Minimum number of samples required to be at a leaf node.
            Defaults to 10 to prevent overfitting.
        clip_quantile (float): Quantile for weight clipping. If 0.05, clips to
            5th and 95th percentiles. If None, uses fixed [0.35, 45.0] range.
        seed (int, optional): Random seed for reproducible results.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int | None = 5,
        min_samples_leaf: int = 10,
        clip_quantile: float = 0.05,
        seed: int | None = None,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.clip_quantile = clip_quantile
        self.seed = seed
        self._w_calib = None
        self._w_test = None
        self._is_fitted = False

    def fit(self, calibration_samples: np.ndarray, test_samples: np.ndarray) -> None:
        """Fit the Random Forest weight estimator on calibration and test samples.

        Args:
            calibration_samples: Array of calibration data samples.
            test_samples: Array of test data samples.

        Raises:
            ValueError: If calibration_samples is empty.
        """
        if calibration_samples.shape[0] == 0:
            raise ValueError("Calibration samples are empty. Cannot compute weights.")

        # Label calibration samples as 0, test samples as 1
        calib_labeled = np.hstack(
            (
                calibration_samples,
                np.zeros((calibration_samples.shape[0], 1)),
            )
        )
        test_labeled = np.hstack((test_samples, np.ones((test_samples.shape[0], 1))))

        # Combine and shuffle
        joint_labeled = np.vstack((calib_labeled, test_labeled))
        rng = np.random.default_rng(seed=self.seed)
        rng.shuffle(joint_labeled)

        x_joint = joint_labeled[:, :-1]
        y_joint = joint_labeled[:, -1]

        # Build Random Forest classifier
        model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf,
            random_state=self.seed,
            class_weight="balanced",
            n_jobs=-1,  # Use all available cores
        )
        model.fit(x_joint, y_joint)

        # Compute probabilities
        calib_prob = model.predict_proba(calibration_samples)
        test_prob = model.predict_proba(test_samples)

        # Compute density ratios w(z) = p_test(z) / p_calib(z)
        # p_calib(z) = P(label=0 | z) ; p_test(z) = P(label=1 | z)
        w_calib = calib_prob[:, 1] / (calib_prob[:, 0] + 1e-9)
        w_test = test_prob[:, 1] / (test_prob[:, 0] + 1e-9)

        # Apply clipping
        if self.clip_quantile is not None:
            # Adaptive clipping based on percentiles
            all_weights = np.concatenate([w_calib, w_test])
            lower_bound = np.percentile(all_weights, self.clip_quantile * 100)
            upper_bound = np.percentile(all_weights, (1 - self.clip_quantile) * 100)

            self._w_calib = np.clip(w_calib, lower_bound, upper_bound)
            self._w_test = np.clip(w_test, lower_bound, upper_bound)
        else:
            # Fixed clipping (original behavior)
            self._w_calib = np.clip(w_calib, 0.35, 45.0)
            self._w_test = np.clip(w_test, 0.35, 45.0)

        self._is_fitted = True

    def get_weights(self) -> tuple[np.ndarray, np.ndarray]:
        """Return computed weights.

        Returns:
            Tuple of (calibration_weights, test_weights).

        Raises:
            RuntimeError: If fit() has not been called.
        """
        if not self._is_fitted:
            raise RuntimeError("Must call fit() before get_weights()")

        return self._w_calib.copy(), self._w_test.copy()
