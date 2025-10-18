
"""
Inference script for the traditional baseline model (Logistic Regression).

This script allows you to make predictions on new text samples using the trained
baseline model. It mirrors the argument parsing of the main inference.py script.

Usage:
    # Single example
    python inference_baseline.py --text "Please provide your social security number for verification."

    # Multiple examples
    python inference_baseline.py --text "Hello world" "What is your email?"

    # From file (one text per line)
    python inference_baseline.py --file input_texts.txt

    # Interactive mode
    python inference_baseline.py --interactive
"""

import argparse
import logging
import joblib
import time
from pathlib import Path
from typing import List, Dict, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseline_inference.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaselineClassifier:
    """
    A wrapper class for the trained scikit-learn baseline model.
    """

    def __init__(self, model_path: str = "./baseline_model"):
        """
        Initialize the classifier with the trained model and vectorizer.

        Args:
            model_path (str): Path to the directory containing the saved model artifacts.
        """
        self.model_path = Path(model_path)
        self.model = None
        self.vectorizer = None

        logger.info(f"Initializing Baseline Classifier...")
        self._load_model()

    def _load_model(self):
        """Load the trained model and TF-IDF vectorizer from disk."""
        try:
            model_file = self.model_path / "logistic_regression_model.joblib"
            vectorizer_file = self.model_path / "tfidf_vectorizer.joblib"
            logger.info(f"Loading model from {model_file}...")
            self.model = joblib.load(model_file)
            logger.info(f"Loading vectorizer from {vectorizer_file}...")
            self.vectorizer = joblib.load(vectorizer_file)

            logger.info("Baseline model and vectorizer loaded successfully!")

        except FileNotFoundError as e:
            logger.error(f"Failed to load model artifact: {e}")
            logger.error("Please ensure the baseline model has been trained and saved correctly using train_baseline.py.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading the model: {e}")
            raise

    def predict_single(self, text: str, return_probabilities: bool = False) -> Dict:
        """
        Predict the class for a single text sample.
        """
        start_time = time.time()
        
        # Scikit-learn expects a list or iterable
        text_features = self.vectorizer.transform([text])

        # Get prediction and probabilities
        predicted_label = self.model.predict(text_features)[0]
        probabilities = self.model.predict_proba(text_features)[0]
        confidence = probabilities.max()
        
        inference_time = time.time() - start_time

        # Prepare results
        result = {
            'text': text,
            'predicted_label': predicted_label,
            'confidence': confidence,
            'predicted_class_id': self.model.classes_.tolist().index(predicted_label),
            'inference_time': inference_time,
        }

        if return_probabilities:
            result['probabilities'] = {
                label: prob
                for label, prob in zip(self.model.classes_, probabilities)
            }

        return result

    def predict_batch(self, texts: List[str], return_probabilities: bool = False) -> List[Dict]:
        """
        Predict classes for multiple text samples.
        """
        logger.info(f"Processing batch of {len(texts)} texts...")
        start_time = time.time()
        
        text_features = self.vectorizer.transform(texts)

        # Get predictions and probabilities
        predicted_labels = self.model.predict(text_features)
        all_probabilities = self.model.predict_proba(text_features)
        confidences = all_probabilities.max(axis=1)
        
        total_inference_time = time.time() - start_time
        avg_inference_time = total_inference_time / len(texts)

        # Prepare results
        results = []
        for i, text in enumerate(texts):
            result = {
                'text': text,
                'predicted_label': predicted_labels[i],
                'confidence': confidences[i],
                'inference_time': avg_inference_time,
            }

            if return_probabilities:
                result['probabilities'] = {
                    label: prob
                    for label, prob in zip(self.model.classes_, all_probabilities[i])
                }

            results.append(result)

        logger.info(f"Batch processing completed! Total time: {total_inference_time:.4f}s, Avg per text: {avg_inference_time:.4f}s")
        return results

    def predict_from_file(self, file_path: str, return_probabilities: bool = False) -> List[Dict]:
        """
        Predict classes for texts from a file (one text per line).
        """
        logger.info(f"Reading texts from {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                texts = [line.strip() for line in f if line.strip()]

            logger.info(f"Loaded {len(texts)} texts from file")
            return self.predict_batch(texts, return_probabilities)

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

def print_results(results: Union[Dict, List[Dict]], show_probabilities: bool = False):
    """Print prediction results in a nice format."""
    if isinstance(results, dict):
        results = [results]

    print("\n" + "="*80)
    print("BASELINE MODEL PREDICTION RESULTS")
    print("="*80)

    for i, result in enumerate(results, 1):
        print(f"\n--- Sample {i} ---")
        print(f"Text: {result['text']}")
        print(f"Predicted Label: {result['predicted_label']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Inference Time: {result['inference_time']:.4f}s")

        if show_probabilities and 'probabilities' in result:
            print("All Probabilities:")
            for label, prob in result['probabilities'].items():
                print(f"  {label}: {prob:.4f}")
        print("-" * 40)

def interactive_mode(classifier: BaselineClassifier):
    """Run the classifier in interactive mode."""
    print("\n" + "="*60)
    print("INTERACTIVE BASELINE CLASSIFIER")
    print("="*60)
    print("Enter text to classify (type 'quit' to exit)")
    print("Add '--prob' to see all class probabilities")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nEnter text: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                print("Please enter some text to classify.")
                continue

            show_prob = '--prob' in user_input
            if show_prob:
                user_input = user_input.replace('--prob', '').strip()

            result = classifier.predict_single(user_input, return_probabilities=show_prob)

            print(f"\nPredicted Label: {result['predicted_label']}")
            print(f"Confidence: {result['confidence']:.4f}")
            print(f"Inference Time: {result['inference_time']:.4f}s")

            if show_prob and 'probabilities' in result:
                print("All Probabilities:")
                for label, prob in result['probabilities'].items():
                    print(f"  {label}: {prob:.4f}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    """Main function to handle command line arguments and run inference."""
    parser = argparse.ArgumentParser(description="Baseline PII Context Classifier Inference")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', nargs='+', help='Text(s) to classify')
    input_group.add_argument('--file', help='File containing texts (one per line)')
    input_group.add_argument('--interactive', action='store_true', help='Run in interactive mode')

    parser.add_argument('--model-path', default="./baseline_model",
                       help='Path to the directory with baseline model artifacts')
    parser.add_argument('--probabilities', action='store_true',
                       help='Show probabilities for all classes')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress logging output')

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    try:
        classifier = BaselineClassifier(args.model_path)

        results = []
        if args.interactive:
            interactive_mode(classifier)
            return 0
        elif args.file:
            results = classifier.predict_from_file(args.file, args.probabilities)
        elif args.text:
            if len(args.text) == 1:
                results = classifier.predict_single(args.text[0], args.probabilities)
            else:
                results = classifier.predict_batch(args.text, args.probabilities)

        print_results(results, args.probabilities)

        if args.output:
            import json
            # Convert numpy types to native python types for json serialization
            if isinstance(results, list):
                for res in results:
                    res['confidence'] = float(res['confidence'])
                    res['inference_time'] = float(res['inference_time'])
            else:
                results['confidence'] = float(results['confidence'])
                results['inference_time'] = float(results['inference_time'])

            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")

    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
