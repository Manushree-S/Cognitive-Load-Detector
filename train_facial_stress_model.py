"""
Production training script for facial stress detection using Scikit-Learn,
OpenCV, and MediaPipe FaceMesh.

Supported datasets:
1. Image directory:
   dataset/
     Stressed/*.jpg
     Relaxed/*.jpg

2. CSV with image paths:
   label,image_path
   Stressed,images/student_001.jpg
   Relaxed,images/student_002.jpg

3. CSV with MediaPipe-style landmark coordinates:
   label,x_33,y_33,x_160,y_160,... or label,lm_33_x,lm_33_y,...

The script extracts normalized facial geometry features, performs a stratified
80/10/10 train/validation/test split, tunes a RandomForest ensemble for high
recall on the Stressed class, evaluates it, tunes a decision threshold to reduce
false negatives, and serializes a Django-ready inference bundle with joblib.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    make_scorer,
    precision_recall_curve,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    import cv2
except ImportError as exc:
    raise ImportError(
        "OpenCV is required. Install it with: pip install opencv-python"
    ) from exc

try:
    import mediapipe as mp
except ImportError as exc:
    raise ImportError(
        "MediaPipe is required. Install it with: pip install mediapipe"
    ) from exc


RANDOM_STATE = 42
STRESSED_LABEL = "Stressed"
RELAXED_LABEL = "Relaxed"
EPSILON = 1e-8

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# MediaPipe FaceMesh indices.
LEFT_EYE_EAR = (33, 160, 158, 133, 153, 144)
RIGHT_EYE_EAR = (362, 385, 387, 263, 373, 380)
LEFT_EYEBROW = (70, 63, 105, 66, 107)
RIGHT_EYEBROW = (336, 296, 334, 293, 300)
LEFT_UPPER_EYE = (159, 158, 157)
RIGHT_UPPER_EYE = (386, 387, 388)
LEFT_EYE_CENTER_POINTS = (33, 133)
RIGHT_EYE_CENTER_POINTS = (362, 263)
MOUTH_CORNERS = (61, 291)
UPPER_LOWER_LIP = (13, 14)
FACE_WIDTH_POINTS = (234, 454)

FEATURE_NAMES = [
    "left_ear",
    "right_ear",
    "mean_ear",
    "ear_asymmetry",
    "left_eyebrow_eye_distance",
    "right_eyebrow_eye_distance",
    "mean_eyebrow_eye_distance",
    "eyebrow_eye_asymmetry",
    "mouth_width_ratio",
    "mouth_opening_ratio",
    "lip_tension_ratio",
]

IMAGE_PATH_CANDIDATES = (
    "image_path",
    "path",
    "filepath",
    "file_path",
    "filename",
    "file",
    "image",
)


@dataclass(frozen=True)
class TrainingMetadata:
    feature_names: List[str]
    class_labels: List[str]
    stressed_probability_threshold: float
    validation_stressed_recall_at_threshold: float
    validation_false_negatives_at_threshold: int
    test_stressed_false_negatives: int
    test_stressed_recall: float
    train_rows: int
    validation_rows: int
    test_rows: int
    dropped_rows_without_face_or_features: int
    best_grid_params: Dict[str, object]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train a robust facial stress detector from labeled face images or "
            "facial landmark coordinate CSV data."
        )
    )
    parser.add_argument(
        "--dataset-path",
        required=True,
        type=Path,
        help="Path to a labeled image directory or CSV dataset.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("model_artifacts/facial_stress_detector"),
        type=Path,
        help="Directory where trained artifacts will be saved.",
    )
    parser.add_argument(
        "--label-column",
        default="label",
        help="CSV label column name. Ignored for image-folder datasets.",
    )
    parser.add_argument(
        "--image-path-column",
        default=None,
        help=(
            "CSV image path column name. If omitted, common names such as "
            "image_path, path, filename, and image are auto-detected."
        ),
    )
    parser.add_argument(
        "--min-stressed-recall",
        default=0.92,
        type=float,
        help=(
            "Target minimum Stressed recall when tuning the decision threshold. "
            "The script chooses the highest-precision threshold that reaches "
            "this recall if the validation data allows it."
        ),
    )
    parser.add_argument(
        "--false-negative-weight",
        default=4.0,
        type=float,
        help="Class weight applied to Stressed during RandomForest training.",
    )
    parser.add_argument(
        "--grid-search-jobs",
        default=-1,
        type=int,
        help="Parallel jobs used by GridSearchCV.",
    )
    return parser.parse_args()


def normalize_label(raw_label: object) -> str:
    value = str(raw_label).strip().lower().replace("-", "_").replace(" ", "_")
    stressed_values = {
        "stressed",
        "stress",
        "high_stress",
        "high",
        "tense",
        "anxious",
        "1",
        "true",
    }
    relaxed_values = {
        "relaxed",
        "relax",
        "calm",
        "neutral",
        "normal",
        "low_stress",
        "low",
        "0",
        "false",
    }
    if value in stressed_values:
        return STRESSED_LABEL
    if value in relaxed_values:
        return RELAXED_LABEL
    raise ValueError(
        f"Unsupported label '{raw_label}'. Use labels equivalent to "
        f"{STRESSED_LABEL!r} or {RELAXED_LABEL!r}."
    )


def euclidean(point_a: np.ndarray, point_b: np.ndarray) -> float:
    return float(np.linalg.norm(point_a - point_b))


def mean_point(landmarks: Dict[int, np.ndarray], indices: Iterable[int]) -> np.ndarray:
    return np.mean([landmarks[index] for index in indices], axis=0)


def required_landmark_indices() -> List[int]:
    indices = set()
    for group in (
        LEFT_EYE_EAR,
        RIGHT_EYE_EAR,
        LEFT_EYEBROW,
        RIGHT_EYEBROW,
        LEFT_UPPER_EYE,
        RIGHT_UPPER_EYE,
        LEFT_EYE_CENTER_POINTS,
        RIGHT_EYE_CENTER_POINTS,
        MOUTH_CORNERS,
        UPPER_LOWER_LIP,
        FACE_WIDTH_POINTS,
    ):
        indices.update(group)
    return sorted(indices)


def eye_aspect_ratio(
    landmarks: Dict[int, np.ndarray], eye_indices: Sequence[int]
) -> float:
    p1, p2, p3, p4, p5, p6 = [landmarks[index] for index in eye_indices]
    vertical_distance = euclidean(p2, p6) + euclidean(p3, p5)
    horizontal_distance = 2.0 * euclidean(p1, p4)
    return vertical_distance / max(horizontal_distance, EPSILON)


def geometric_features_from_landmarks(landmarks: Dict[int, np.ndarray]) -> np.ndarray:
    missing = [index for index in required_landmark_indices() if index not in landmarks]
    if missing:
        raise ValueError(f"Missing required FaceMesh landmark indices: {missing}")

    left_eye_center = mean_point(landmarks, LEFT_EYE_CENTER_POINTS)
    right_eye_center = mean_point(landmarks, RIGHT_EYE_CENTER_POINTS)
    interocular_distance = euclidean(left_eye_center, right_eye_center)
    face_width = euclidean(landmarks[FACE_WIDTH_POINTS[0]], landmarks[FACE_WIDTH_POINTS[1]])
    normalizer = max(interocular_distance, face_width * 0.45, EPSILON)

    left_ear = eye_aspect_ratio(landmarks, LEFT_EYE_EAR)
    right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE_EAR)
    mean_ear = (left_ear + right_ear) / 2.0
    ear_asymmetry = abs(left_ear - right_ear)

    left_brow_center = mean_point(landmarks, LEFT_EYEBROW)
    right_brow_center = mean_point(landmarks, RIGHT_EYEBROW)
    left_upper_eye = mean_point(landmarks, LEFT_UPPER_EYE)
    right_upper_eye = mean_point(landmarks, RIGHT_UPPER_EYE)
    left_eyebrow_eye_distance = euclidean(left_brow_center, left_upper_eye) / normalizer
    right_eyebrow_eye_distance = euclidean(right_brow_center, right_upper_eye) / normalizer
    mean_eyebrow_eye_distance = (
        left_eyebrow_eye_distance + right_eyebrow_eye_distance
    ) / 2.0
    eyebrow_eye_asymmetry = abs(left_eyebrow_eye_distance - right_eyebrow_eye_distance)

    mouth_width = euclidean(landmarks[MOUTH_CORNERS[0]], landmarks[MOUTH_CORNERS[1]])
    lip_gap = euclidean(landmarks[UPPER_LOWER_LIP[0]], landmarks[UPPER_LOWER_LIP[1]])
    mouth_width_ratio = mouth_width / normalizer
    mouth_opening_ratio = lip_gap / max(mouth_width, EPSILON)
    lip_tension_ratio = mouth_width_ratio / max(mouth_opening_ratio, EPSILON)

    return np.array(
        [
            left_ear,
            right_ear,
            mean_ear,
            ear_asymmetry,
            left_eyebrow_eye_distance,
            right_eyebrow_eye_distance,
            mean_eyebrow_eye_distance,
            eyebrow_eye_asymmetry,
            mouth_width_ratio,
            mouth_opening_ratio,
            lip_tension_ratio,
        ],
        dtype=np.float32,
    )


class FaceMeshExtractor:
    def __init__(self) -> None:
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )

    def close(self) -> None:
        self._face_mesh.close()

    def extract_landmarks_from_bgr_image(
        self, image: np.ndarray
    ) -> Optional[Dict[int, np.ndarray]]:
        if image is None or image.size == 0:
            return None

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self._face_mesh.process(rgb_image)
        if not result.multi_face_landmarks:
            return None

        height, width = rgb_image.shape[:2]
        face_landmarks = result.multi_face_landmarks[0].landmark
        return {
            index: np.array(
                [landmark.x * width, landmark.y * height, landmark.z * width],
                dtype=np.float32,
            )
            for index, landmark in enumerate(face_landmarks)
        }

    def extract_features_from_bgr_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        landmarks = self.extract_landmarks_from_bgr_image(image)
        if landmarks is None:
            return None
        return geometric_features_from_landmarks(landmarks)

    def extract_landmarks_from_image(self, image_path: Path) -> Optional[Dict[int, np.ndarray]]:
        image = cv2.imread(str(image_path))
        if image is None:
            warnings.warn(f"OpenCV could not read image: {image_path}", RuntimeWarning)
            return None

        landmarks = self.extract_landmarks_from_bgr_image(image)
        if landmarks is None:
            warnings.warn(f"No face detected in image: {image_path}", RuntimeWarning)
            return None
        return landmarks

    def extract_features_from_image(self, image_path: Path) -> Optional[np.ndarray]:
        landmarks = self.extract_landmarks_from_image(image_path)
        if landmarks is None:
            return None
        return geometric_features_from_landmarks(landmarks)


def discover_image_path_column(
    dataframe: pd.DataFrame, explicit_column: Optional[str]
) -> Optional[str]:
    if explicit_column is not None:
        if explicit_column not in dataframe.columns:
            raise ValueError(f"Image path column '{explicit_column}' was not found.")
        return explicit_column
    for candidate in IMAGE_PATH_CANDIDATES:
        if candidate in dataframe.columns:
            return candidate
    return None


def resolve_image_path(raw_path: object, dataset_path: Path) -> Path:
    path = Path(str(raw_path))
    if path.is_absolute():
        return path
    return dataset_path.parent / path


def landmark_column_lookup(columns: Sequence[str]) -> Dict[Tuple[int, str], str]:
    lookup: Dict[Tuple[int, str], str] = {}
    axes = ("x", "y", "z")
    for column in columns:
        lowered = column.strip().lower()
        for index in required_landmark_indices():
            patterns = (
                f"x_{index}",
                f"y_{index}",
                f"z_{index}",
                f"{index}_x",
                f"{index}_y",
                f"{index}_z",
                f"lm_{index}_x",
                f"lm_{index}_y",
                f"lm_{index}_z",
                f"landmark_{index}_x",
                f"landmark_{index}_y",
                f"landmark_{index}_z",
                f"x{index}",
                f"y{index}",
                f"z{index}",
            )
            if lowered in patterns:
                for axis in axes:
                    if lowered.endswith(f"_{axis}") or lowered == f"{axis}_{index}" or lowered == f"{axis}{index}":
                        lookup[(index, axis)] = column
    return lookup


def landmarks_from_dataframe_row(
    row: pd.Series, lookup: Dict[Tuple[int, str], str]
) -> Optional[Dict[int, np.ndarray]]:
    landmarks: Dict[int, np.ndarray] = {}
    for index in required_landmark_indices():
        x_column = lookup.get((index, "x"))
        y_column = lookup.get((index, "y"))
        z_column = lookup.get((index, "z"))
        if x_column is None or y_column is None:
            return None
        x_value = row[x_column]
        y_value = row[y_column]
        z_value = row[z_column] if z_column is not None else 0.0
        if pd.isna(x_value) or pd.isna(y_value) or pd.isna(z_value):
            return None
        landmarks[index] = np.array(
            [float(x_value), float(y_value), float(z_value)], dtype=np.float32
        )
    return landmarks


def load_from_image_directory(dataset_path: Path) -> Tuple[pd.DataFrame, int]:
    rows: List[Dict[str, object]] = []
    extractor = FaceMeshExtractor()
    dropped = 0
    try:
        for class_dir in sorted([path for path in dataset_path.iterdir() if path.is_dir()]):
            label = normalize_label(class_dir.name)
            image_paths = sorted(
                path
                for path in class_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
            )
            for image_path in image_paths:
                features = extractor.extract_features_from_image(image_path)
                if features is None:
                    dropped += 1
                    continue
                row = {name: float(value) for name, value in zip(FEATURE_NAMES, features)}
                row["label"] = label
                row["source_path"] = str(image_path)
                rows.append(row)
    finally:
        extractor.close()

    if not rows:
        raise ValueError(
            f"No usable face images found in {dataset_path}. Expected subfolders "
            f"named {STRESSED_LABEL} and {RELAXED_LABEL}."
        )
    return pd.DataFrame(rows), dropped


def load_from_csv(
    dataset_path: Path, label_column: str, image_path_column: Optional[str]
) -> Tuple[pd.DataFrame, int]:
    dataframe = pd.read_csv(dataset_path)
    if label_column not in dataframe.columns:
        raise ValueError(f"Label column '{label_column}' was not found in {dataset_path}.")

    dataframe = dataframe.copy()
    dataframe["label"] = dataframe[label_column].map(normalize_label)
    detected_image_column = discover_image_path_column(dataframe, image_path_column)
    rows: List[Dict[str, object]] = []
    dropped = 0

    if detected_image_column is not None:
        extractor = FaceMeshExtractor()
        try:
            for _, row in dataframe.iterrows():
                image_path = resolve_image_path(row[detected_image_column], dataset_path)
                features = extractor.extract_features_from_image(image_path)
                if features is None:
                    dropped += 1
                    continue
                output_row = {
                    name: float(value) for name, value in zip(FEATURE_NAMES, features)
                }
                output_row["label"] = row["label"]
                output_row["source_path"] = str(image_path)
                rows.append(output_row)
        finally:
            extractor.close()
    else:
        lookup = landmark_column_lookup(dataframe.columns)
        for _, row in dataframe.iterrows():
            landmarks = landmarks_from_dataframe_row(row, lookup)
            if landmarks is None:
                dropped += 1
                continue
            features = geometric_features_from_landmarks(landmarks)
            output_row = {name: float(value) for name, value in zip(FEATURE_NAMES, features)}
            output_row["label"] = row["label"]
            rows.append(output_row)

    if not rows:
        raise ValueError(
            "No usable rows were produced. Provide either a valid image path column "
            "or MediaPipe landmark coordinate columns for the required indices."
        )
    return pd.DataFrame(rows), dropped


def load_dataset(
    dataset_path: Path, label_column: str, image_path_column: Optional[str]
) -> Tuple[pd.DataFrame, int]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")
    if dataset_path.is_dir():
        return load_from_image_directory(dataset_path)
    if dataset_path.suffix.lower() == ".csv":
        return load_from_csv(dataset_path, label_column, image_path_column)
    raise ValueError("Dataset path must be a directory of images or a CSV file.")


def validate_dataset(dataframe: pd.DataFrame) -> None:
    labels = set(dataframe["label"].unique())
    expected = {STRESSED_LABEL, RELAXED_LABEL}
    if labels != expected:
        raise ValueError(
            f"Training requires both classes {sorted(expected)}. Found: {sorted(labels)}"
        )
    class_counts = dataframe["label"].value_counts()
    too_small = class_counts[class_counts < 5]
    if not too_small.empty:
        raise ValueError(
            "Each class needs at least 5 usable samples for stratified 80/10/10 "
            f"splitting and cross-validation. Counts: {class_counts.to_dict()}"
        )


def split_dataset(
    dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df, temp_df = train_test_split(
        dataframe,
        test_size=0.20,
        stratify=dataframe["label"],
        random_state=RANDOM_STATE,
    )
    validation_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        stratify=temp_df["label"],
        random_state=RANDOM_STATE,
    )
    return (
        train_df.reset_index(drop=True),
        validation_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def build_training_pipeline(
    false_negative_weight: float,
) -> Tuple[Pipeline, Dict[str, List[object]]]:
    class_weight = {
        RELAXED_LABEL: 1.0,
        STRESSED_LABEL: float(false_negative_weight),
    }
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    class_weight=class_weight,
                ),
            ),
        ]
    )
    parameter_grid = {
        "classifier__n_estimators": [300, 600],
        "classifier__max_depth": [None, 8, 16],
        "classifier__min_samples_split": [2, 5],
        "classifier__min_samples_leaf": [1, 2, 4],
        "classifier__max_features": ["sqrt", "log2", None],
    }
    return pipeline, parameter_grid


def choose_cv_splits(y_train: pd.Series) -> int:
    minimum_class_count = int(y_train.value_counts().min())
    return max(2, min(5, minimum_class_count))


def train_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    false_negative_weight: float,
    grid_search_jobs: int,
) -> GridSearchCV:
    pipeline, parameter_grid = build_training_pipeline(false_negative_weight)
    cv_splits = choose_cv_splits(y_train)
    scorers = {
        "stressed_recall": make_scorer(recall_score, pos_label=STRESSED_LABEL),
        "weighted_f1": make_scorer(f1_score, average="weighted"),
    }
    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=parameter_grid,
        scoring=scorers,
        refit="stressed_recall",
        cv=StratifiedKFold(
            n_splits=cv_splits, shuffle=True, random_state=RANDOM_STATE
        ),
        n_jobs=grid_search_jobs,
        verbose=2,
        return_train_score=True,
    )
    grid_search.fit(x_train, y_train)
    return grid_search


def stressed_probability(model: BaseEstimator, x_values: pd.DataFrame) -> np.ndarray:
    if not hasattr(model, "predict_proba"):
        raise TypeError("The trained estimator must support predict_proba.")
    classes = list(model.classes_)
    stressed_index = classes.index(STRESSED_LABEL)
    return model.predict_proba(x_values)[:, stressed_index]


def predict_with_threshold(
    model: BaseEstimator, x_values: pd.DataFrame, threshold: float
) -> np.ndarray:
    probabilities = stressed_probability(model, x_values)
    return np.where(probabilities >= threshold, STRESSED_LABEL, RELAXED_LABEL)


def tune_threshold_for_false_negatives(
    model: BaseEstimator,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
    min_stressed_recall: float,
) -> Tuple[float, float, int]:
    y_binary = (y_validation == STRESSED_LABEL).astype(int).to_numpy()
    probabilities = stressed_probability(model, x_validation)
    precision, recall, thresholds = precision_recall_curve(y_binary, probabilities)

    candidate_thresholds = np.r_[thresholds, 1.0]
    candidate_precision = precision[:-1].tolist() + [precision[-1]]
    candidate_recall = recall[:-1].tolist() + [recall[-1]]

    candidates: List[Tuple[float, float, float, int]] = []
    stressed_count = int(np.sum(y_binary == 1))
    for threshold, candidate_p, candidate_r in zip(
        candidate_thresholds, candidate_precision, candidate_recall
    ):
        validation_predictions = np.where(
            probabilities >= threshold, STRESSED_LABEL, RELAXED_LABEL
        )
        false_negatives = int(
            np.sum(
                (y_validation.to_numpy() == STRESSED_LABEL)
                & (validation_predictions == RELAXED_LABEL)
            )
        )
        if candidate_r >= min_stressed_recall:
            candidates.append(
                (
                    float(threshold),
                    float(candidate_p),
                    float(candidate_r),
                    false_negatives,
                )
            )

    if candidates:
        candidates.sort(key=lambda item: (-item[2], item[3], -item[1], -item[0]))
        threshold, _, stressed_recall, false_negatives = candidates[0]
    else:
        best_index = int(np.argmax(candidate_recall))
        threshold = float(candidate_thresholds[best_index])
        stressed_recall = float(candidate_recall[best_index])
        false_negatives = max(
            0, stressed_count - int(round(stressed_count * stressed_recall))
        )

    threshold = min(max(threshold, 0.0), 1.0)
    return threshold, stressed_recall, int(false_negatives)


def evaluate_model(
    model: BaseEstimator,
    x_values: pd.DataFrame,
    y_true: pd.Series,
    threshold: float,
    split_name: str,
) -> Tuple[np.ndarray, np.ndarray, int, float]:
    y_pred = predict_with_threshold(model, x_values, threshold)
    labels = [RELAXED_LABEL, STRESSED_LABEL]
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    print(f"\n=== {split_name} Classification Report ===")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=labels,
            target_names=labels,
            digits=4,
            zero_division=0,
        )
    )
    print(f"=== {split_name} Confusion Matrix ===")
    matrix_df = pd.DataFrame(
        matrix,
        index=[f"actual_{label}" for label in labels],
        columns=[f"predicted_{label}" for label in labels],
    )
    print(matrix_df.to_string())

    stressed_false_negatives = int(matrix[1, 0])
    stressed_recall = recall_score(
        y_true,
        y_pred,
        pos_label=STRESSED_LABEL,
        zero_division=0,
    )
    print(
        f"{split_name} stressed false negatives: {stressed_false_negatives} "
        f"(missed highly stressed students)"
    )
    print(f"{split_name} stressed recall: {stressed_recall:.4f}")
    return y_pred, matrix, stressed_false_negatives, float(stressed_recall)


def save_artifacts(
    output_dir: Path,
    best_model: BaseEstimator,
    threshold: float,
    validation_recall: float,
    validation_false_negatives: int,
    test_false_negatives: int,
    test_recall: float,
    train_rows: int,
    validation_rows: int,
    test_rows: int,
    dropped_rows: int,
    best_grid_params: Dict[str, object],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = TrainingMetadata(
        feature_names=FEATURE_NAMES,
        class_labels=[RELAXED_LABEL, STRESSED_LABEL],
        stressed_probability_threshold=threshold,
        validation_stressed_recall_at_threshold=validation_recall,
        validation_false_negatives_at_threshold=validation_false_negatives,
        test_stressed_false_negatives=test_false_negatives,
        test_stressed_recall=test_recall,
        train_rows=train_rows,
        validation_rows=validation_rows,
        test_rows=test_rows,
        dropped_rows_without_face_or_features=dropped_rows,
        best_grid_params=best_grid_params,
    )

    bundle = {
        "pipeline": best_model,
        "feature_names": FEATURE_NAMES,
        "class_labels": [RELAXED_LABEL, STRESSED_LABEL],
        "stressed_probability_threshold": threshold,
        "metadata": asdict(metadata),
    }

    bundle_path = output_dir / "facial_stress_detector.joblib"
    metadata_path = output_dir / "metadata.json"
    joblib.dump(bundle, bundle_path)
    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(asdict(metadata), file, indent=2)

    print(f"\nSaved model bundle: {bundle_path.resolve()}")
    print(f"Saved metadata: {metadata_path.resolve()}")
    print(
        "\nDjango loading example:\n"
        "import joblib\n"
        f"bundle = joblib.load(r'{bundle_path.resolve()}')\n"
        "model = bundle['pipeline']\n"
        "threshold = bundle['stressed_probability_threshold']\n"
    )


def main() -> int:
    args = parse_args()
    np.random.seed(RANDOM_STATE)

    dataset, dropped_rows = load_dataset(
        args.dataset_path, args.label_column, args.image_path_column
    )
    validate_dataset(dataset)

    print("\nUsable dataset rows by class:")
    print(dataset["label"].value_counts().to_string())
    if dropped_rows:
        print(f"Dropped rows/images without usable face landmarks: {dropped_rows}")

    train_df, validation_df, test_df = split_dataset(dataset)
    x_train = train_df[FEATURE_NAMES]
    y_train = train_df["label"]
    x_validation = validation_df[FEATURE_NAMES]
    y_validation = validation_df["label"]
    x_test = test_df[FEATURE_NAMES]
    y_test = test_df["label"]

    print(
        f"\nSplit sizes: train={len(train_df)}, validation={len(validation_df)}, "
        f"test={len(test_df)}"
    )

    grid_search = train_model(
        x_train=x_train,
        y_train=y_train,
        false_negative_weight=args.false_negative_weight,
        grid_search_jobs=args.grid_search_jobs,
    )
    best_model = grid_search.best_estimator_
    print("\nBest GridSearchCV parameters:")
    print(json.dumps(grid_search.best_params_, indent=2))
    print(f"Best CV stressed recall: {grid_search.best_score_:.4f}")

    (
        threshold,
        validation_recall,
        validation_false_negatives,
    ) = tune_threshold_for_false_negatives(
        best_model,
        x_validation,
        y_validation,
        min_stressed_recall=args.min_stressed_recall,
    )
    print(
        f"\nChosen Stressed probability threshold: {threshold:.4f} "
        f"(validation stressed recall={validation_recall:.4f}, "
        f"false negatives={validation_false_negatives})"
    )

    evaluate_model(best_model, x_validation, y_validation, threshold, "Validation")
    _, _, test_false_negatives, test_recall = evaluate_model(
        best_model, x_test, y_test, threshold, "Test"
    )

    save_artifacts(
        output_dir=args.output_dir,
        best_model=best_model,
        threshold=threshold,
        validation_recall=validation_recall,
        validation_false_negatives=validation_false_negatives,
        test_false_negatives=test_false_negatives,
        test_recall=test_recall,
        train_rows=len(train_df),
        validation_rows=len(validation_df),
        test_rows=len(test_df),
        dropped_rows=dropped_rows,
        best_grid_params=grid_search.best_params_,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"\nTraining failed: {error}", file=sys.stderr)
        raise
