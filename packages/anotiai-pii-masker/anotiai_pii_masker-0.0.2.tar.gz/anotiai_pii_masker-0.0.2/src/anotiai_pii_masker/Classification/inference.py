"""
Inference script for the PII Context Classifier.

This script allows you to make predictions on new text samples using the trained model.
Supports both single examples and batch processing.

Usage:
    # Single example
    python inference.py --text "Please provide your social security number for verification."
    
    # Multiple examples
    python inference.py --text "Hello world" "What is your email?" "The weather is nice today"
    
    # From file (one text per line)
    python inference.py --file input_texts.txt
    
    # Interactive mode
    python inference.py --interactive
"""

import argparse
import logging
import torch
import pandas as pd
import time
from typing import List, Dict, Union
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from . import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inference.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PiiContextClassifier:
    """
    A wrapper class for the trained PII Context Classifier model.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the classifier with the trained model.
        
        Args:
            model_path (str): Path to the saved model. Defaults to config.MODEL_SAVE_PATH
        """
        self.model_path = model_path or config.MODEL_SAVE_PATH
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None
        self.id_to_label = {v: k for k, v in config.LABEL_MAP.items()}
        
        logger.info(f"Initializing PII Context Classifier...")
        logger.info(f"Using device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and tokenizer."""
        try:
            logger.info(f"Loading model from {self.model_path}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("Model loaded successfully!")
            logger.info(f"Model has {sum(p.numel() for p in self.model.parameters())} parameters")
            logger.info(f"Available labels: {list(self.id_to_label.values())}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.error("Please ensure the model has been trained and saved correctly.")
            raise
    
    def predict_single(self, text: str, return_probabilities: bool = False) -> Dict:
        """
        Predict the class for a single text sample.
        
        Args:
            text (str): Input text to classify
            return_probabilities (bool): Whether to return class probabilities
            
        Returns:
            Dict: Prediction results with label, confidence, and optionally probabilities
        """
        start_time = time.time()
        
        # Tokenize the input
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=config.MAX_LEN,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Make prediction
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            predicted_class_id = torch.argmax(logits, dim=-1).item()
            confidence = probabilities[0][predicted_class_id].item()
        
        inference_time = time.time() - start_time
        
        # Prepare results
        result = {
            'text': text,
            'predicted_label': self.id_to_label[predicted_class_id],
            'confidence': confidence,
            'predicted_class_id': predicted_class_id,
            'inference_time': inference_time
        }
        
        if return_probabilities:
            result['probabilities'] = {
                self.id_to_label[i]: prob.item() 
                for i, prob in enumerate(probabilities[0])
            }
        
        return result
    
    def predict_batch(self, texts: List[str], return_probabilities: bool = False) -> List[Dict]:
        """
        Predict classes for multiple text samples.
        
        Args:
            texts (List[str]): List of input texts to classify
            return_probabilities (bool): Whether to return class probabilities
            
        Returns:
            List[Dict]: List of prediction results
        """
        logger.info(f"Processing batch of {len(texts)} texts...")
        start_time = time.time()
        
        # Tokenize all inputs
        inputs = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=config.MAX_LEN,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Make predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            predicted_class_ids = torch.argmax(logits, dim=-1)
            confidences = torch.max(probabilities, dim=-1)[0]
        
        total_inference_time = time.time() - start_time
        avg_inference_time = total_inference_time / len(texts)
        
        # Prepare results
        results = []
        for i, text in enumerate(texts):
            result = {
                'text': text,
                'predicted_label': self.id_to_label[predicted_class_ids[i].item()],
                'confidence': confidences[i].item(),
                'predicted_class_id': predicted_class_ids[i].item(),
                'inference_time': avg_inference_time
            }
            
            if return_probabilities:
                result['probabilities'] = {
                    self.id_to_label[j]: probabilities[i][j].item() 
                    for j in range(len(self.id_to_label))
                }
            
            results.append(result)
        
        logger.info(f"Batch processing completed! Total time: {total_inference_time:.4f}s, Avg per text: {avg_inference_time:.4f}s")
        return results
    
    def predict_from_file(self, file_path: str, return_probabilities: bool = False) -> List[Dict]:
        """
        Predict classes for texts from a file (one text per line).
        
        Args:
            file_path (str): Path to the input file
            return_probabilities (bool): Whether to return class probabilities
            
        Returns:
            List[Dict]: List of prediction results
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
    print("PREDICTION RESULTS")
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

def interactive_mode(classifier: PiiContextClassifier):
    """Run the classifier in interactive mode."""
    print("\n" + "="*60)
    print("INTERACTIVE PII CONTEXT CLASSIFIER")
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
            
            # Check for probability flag
            show_prob = False
            if user_input.endswith('--prob'):
                show_prob = True
                user_input = user_input[:-6].strip()
            
            # Make prediction
            result = classifier.predict_single(user_input, return_probabilities=show_prob)
            
            # Display result
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
            print(f"Error: {e}")

def main():
    """Main function to handle command line arguments and run inference."""
    parser = argparse.ArgumentParser(description="PII Context Classifier Inference")
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', nargs='+', help='Text(s) to classify')
    input_group.add_argument('--file', help='File containing texts (one per line)')
    input_group.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    # Optional arguments
    parser.add_argument('--model-path', default=config.MODEL_SAVE_PATH, 
                       help='Path to the trained model')
    parser.add_argument('--probabilities', action='store_true', 
                       help='Show probabilities for all classes')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress logging output')
    
    args = parser.parse_args()
    
    # Adjust logging level if quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Initialize classifier
        classifier = PiiContextClassifier(args.model_path)
        
        # Handle different input modes
        if args.interactive:
            interactive_mode(classifier)
            
        elif args.file:
            results = classifier.predict_from_file(args.file, args.probabilities)
            print_results(results, args.probabilities)
            
        elif args.text:
            if len(args.text) == 1:
                result = classifier.predict_single(args.text[0], args.probabilities)
                print_results(result, args.probabilities)
            else:
                results = classifier.predict_batch(args.text, args.probabilities)
                print_results(results, args.probabilities)
        
        # Save results if requested
        if args.output and 'results' in locals():
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
