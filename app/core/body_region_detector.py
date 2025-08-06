import logging
from typing import Dict, Tuple, List
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

class BodyRegionDetector:
    """Detects body regions in medical X-ray images to enforce safety validation."""

    REGION_CHARACTERISTICS: Dict[str, Dict] = {
        'chest': {
            'aspect_ratio_range': (0.7, 1.3),
            'expected_features': ['lung', 'thorax', 'chest', 'cardiac', 'pulmonary', 'rib', 'heart'],
            'density_pattern': 'bimodal',  # two peaks (air / tissue)
            'min_confidence': 0.7,
        },
        'abdomen': {
            'aspect_ratio_range': (0.8, 1.4),
            'expected_features': ['abdomen', 'abdominal', 'bowel', 'pelvis', 'intestine', 'gastric'],
            'density_pattern': 'multimodal',
            'min_confidence': 0.6,
        },
        'extremity': {
            'aspect_ratio_range': (0.3, 3.0),  # elongated
            'expected_features': ['bone', 'joint', 'extremity', 'arm', 'leg', 'hand', 'foot', 'shoulder', 'knee', 'elbow', 'wrist', 'humerus', 'femur'],
            'density_pattern': 'high_contrast',
            'min_confidence': 0.6,
        },
        'skull': {
            'aspect_ratio_range': (0.8, 1.2),
            'expected_features': ['skull', 'cranial', 'head', 'cranium', 'brain'],
            'density_pattern': 'dense',
            'min_confidence': 0.7,
        },
        'spine': {
            'aspect_ratio_range': (0.2, 0.6),
            'expected_features': ['spine', 'vertebra', 'spinal', 'lumbar', 'cervical', 'thoracic'],
            'density_pattern': 'linear',
            'min_confidence': 0.6,
        },
    }

    def detect_body_region(self, image_path: str, vision_labels: List[Dict] | None = None) -> Tuple[str, float, Dict]:
        """Detect probable body region. Returns (region, confidence, debug_info)."""
        logger.info("BodyRegionDetector: analysing %s", image_path)
        try:
            img = Image.open(image_path)
            if img.mode != 'L':
                img = img.convert('L')
            arr = np.array(img)
            h, w = arr.shape
            aspect_ratio = w / h

            char = self._analyse(arr)

            scores: Dict[str, Dict] = {}
            for region, crit in self.REGION_CHARACTERISTICS.items():
                score = 0.0
                details: Dict[str, any] = {}
                ar_min, ar_max = crit['aspect_ratio_range']
                if ar_min <= aspect_ratio <= ar_max:
                    score += 0.3
                    details['aspect_ratio_match'] = True
                # label features
                if vision_labels:
                    matches = []
                    for lbl in vision_labels:
                        txt = lbl.get('description', '').lower()
                        if any(exp in txt for exp in crit['expected_features']):
                            matches.append(txt)
                    if matches:
                        details['label_matches'] = matches
                        score += 0.1 * min(len(matches), 3)
                # density pattern match
                if self._matches_pattern(char, crit['density_pattern']):
                    score += 0.2
                    details['density_match'] = True
                # specific heuristics
                if region == 'chest' and self._is_chest(arr, char):
                    score += 0.3
                    details['chest_specific'] = True
                if region == 'extremity' and self._is_extremity(arr, char):
                    score += 0.3
                    details['extremity_specific'] = True
                scores[region] = {'score': round(min(score, 1.0), 2), 'details': details}
            best_region, best_info = max(scores.items(), key=lambda kv: kv[1]['score'])
            confidence = best_info['score']
            logger.info("BodyRegionDetector result %s (%.2f)", best_region, confidence)
            min_conf = self.REGION_CHARACTERISTICS[best_region]['min_confidence']
            if confidence < min_conf:
                best_region = 'unknown'
            return best_region, confidence, scores
        except Exception as e:
            logger.exception("BodyRegionDetector failed: %s", e)
            return 'unknown', 0.0, {}

    # ---------- helpers ------------
    def _analyse(self, arr: np.ndarray) -> Dict:
        hist = cv2.calcHist([arr], [0], None, [256], [0, 256]).flatten()
        hist = hist / (hist.sum() + 1e-8)
        peaks = [i for i in range(1, 255) if hist[i] > 0.01 and hist[i-1] < hist[i] > hist[i+1]]
        mean = float(arr.mean())
        std = float(arr.std())
        edges = cv2.Canny(arr, 50, 150)
        edge_density = edges.mean()
        return {
            'hist': hist,
            'peaks': peaks,
            'num_peaks': len(peaks),
            'mean': mean,
            'std': std,
            'contrast': std / (mean + 1e-8),
            'edge_density': edge_density,
        }

    def _matches_pattern(self, char: Dict, pattern: str) -> bool:
        if pattern == 'bimodal':
            return 1 <= char['num_peaks'] <= 3 and char['contrast'] > 0.25
        if pattern == 'multimodal':
            return char['num_peaks'] >= 3
        if pattern == 'high_contrast':
            return char['contrast'] > 0.5
        if pattern == 'dense':
            return char['mean'] > 100
        if pattern == 'linear':
            return char['edge_density'] > 0.1
        return False

    def _is_chest(self, arr: np.ndarray, char: Dict) -> bool:
        h, w = arr.shape
        left = arr[:, :w//3]
        right = arr[:, 2*w//3:]
        center = arr[:, w//3:2*w//3]
        return left.mean() < center.mean() and right.mean() < center.mean()

    def _is_extremity(self, arr: np.ndarray, char: Dict) -> bool:
        return char['contrast'] > 0.5 and char['edge_density'] > 0.05

    # validation helper
    def validate_region_match(self, detected: str, requested: str) -> Tuple[bool, str]:
        det = detected.lower().strip()
        req = requested.lower().strip()
        if det == 'unknown':
            return False, "Cannot determine body region from the uploaded image. Please upload a clearer X-ray image."
        if det != req:
            return False, f"⚠️ CRITICAL SAFETY ERROR: You requested {requested} analysis, but the uploaded image appears to be a {detected} X-ray. Analysis blocked."
        return True, ""
