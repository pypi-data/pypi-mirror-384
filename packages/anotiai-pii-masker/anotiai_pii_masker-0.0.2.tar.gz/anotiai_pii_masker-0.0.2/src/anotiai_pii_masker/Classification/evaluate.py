"""
Script to evaluate the fine-tuned model on the held-out test set.

This script performs the following steps:
1. Loads the held-out test set from the path specified in config.py.
2. Loads the best fine-tuned model and tokenizer.
3. Creates a PyTorch Dataset for the test data.
4. Initializes the Trainer.
5. Runs the evaluation and prints the performance metrics.
6. Generates and saves a confusion matrix.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging
from sklearn.metrics import confusion_matrix
from transformers import AutoTokenizer, Trainer, TrainingArguments, AutoModelForSequenceClassification

import config
from dataset import PiiTextDataset
from model import create_model
from train import compute_metrics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the evaluation.
    """
    logger.info("Starting model evaluation on held-out test set...")
    
    # 1. Load Test Data
    logger.info(f"Loading test data from {config.TEST_DATA_PATH}...")
    try:
        test_df = pd.read_csv(config.TEST_DATA_PATH)
        logger.info(f"Successfully loaded {len(test_df)} test samples")
    except FileNotFoundError:
        logger.error(f"Test data file not found at '{config.TEST_DATA_PATH}'.")
        logger.error("Please run train.py first to generate the test set.")
        return

    # Log test set label distribution
    logger.info("Test set label distribution:")
    test_label_counts = test_df['label'].value_counts()
    for label, count in test_label_counts.items():
        logger.info(f"  {label}: {count} samples ({count/len(test_df)*100:.1f}%)")

    # Map labels to IDs
    logger.info("Mapping string labels to integers...")
    test_df['label_id'] = test_df['label'].map(config.LABEL_MAP)
    test_texts = test_df['text'].tolist()
    test_labels = test_df['label_id'].astype(int).tolist()

    # 2. Load Model and Tokenizer
    logger.info(f"Loading trained model and tokenizer from {config.MODEL_SAVE_PATH}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(config.MODEL_SAVE_PATH)
        model = create_model() # Re-create model structure
        model.load_state_dict(torch.load(f"{config.MODEL_SAVE_PATH}/pytorch_model.bin"))
        logger.info("Model and tokenizer loaded successfully")
        logger.info(f"Model has {sum(p.numel() for p in model.parameters())} parameters")
    except OSError:
        logger.error(f"Model not found at '{config.MODEL_SAVE_PATH}'.")
        logger.error("Please run train.py first to train and save a model.")
        return

    # 3. Create Test Dataset
    logger.info(f"Tokenizing test data with max_length={config.MAX_LEN}...")
    test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=config.MAX_LEN)
    test_dataset = PiiTextDataset(test_encodings, test_labels)
    logger.info(f"Created test dataset with {len(test_dataset)} samples")

    # 4. Initialize Trainer
    logger.info("Setting up evaluation trainer...")
    # We only need minimal TrainingArguments for evaluation
    eval_args = TrainingArguments(
        output_dir='./eval_results',
        per_device_eval_batch_size=config.VALID_BATCH_SIZE,
        do_train=False,
        do_eval=True,
    )

    trainer = Trainer(
        model=model,
        args=eval_args,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics
    )

    # 5. Evaluate
    logger.info("Running model evaluation...")
    logger.info("This may take a few minutes depending on your test set size...")
    results = trainer.evaluate()

    logger.info("Evaluation completed successfully!")
    logger.info("\n--- Test Set Evaluation Results ---")
    for key, value in results.items():
        logger.info(f"{key.replace('eval_', '').capitalize():<10}: {value:.4f}")
    logger.info("-------------------------------------")

    # 6. Generate and Save Confusion Matrix
    logger.info("Generating confusion matrix...")
    predictions = trainer.predict(test_dataset)
    predicted_labels = predictions.predictions.argmax(axis=1)
    cm = confusion_matrix(test_labels, predicted_labels)
    
    logger.info("Creating confusion matrix visualization...")
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d', 
                xticklabels=config.LABEL_MAP.keys(), 
                yticklabels=config.LABEL_MAP.keys(),
                cmap="Blues")
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.savefig("confusion_matrix.png")
    logger.info("Confusion matrix saved to confusion_matrix.png")
    logger.info("Evaluation pipeline completed!")

if __name__ == "__main__":
    import torch
    main()
