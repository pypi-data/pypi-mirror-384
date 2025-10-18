"""
Main script to train a traditional ML baseline model (Logistic Regression)
for the PII Context Classifier.
"""

import pandas as pd
import logging
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseline_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define save path for the baseline model
BASELINE_MODEL_SAVE_PATH = Path("./baseline_model")

def main():
    """
    The main function to run the baseline model training and evaluation pipeline.
    """
    logger.info("Starting Traditional Model Baseline training pipeline...")
    BASELINE_MODEL_SAVE_PATH.mkdir(exist_ok=True)

    # 1. Load Data (using the same path as the main training script)
    # IMPORTANT: Update config.DATA_PATH to point to your actual dataset
    # For this example, we'll assume it's pointing to pii_dataset.csv
    data_path = "/home/emms/Downloads/AnotiAI/PII_Detection_System/pii_dataset.csv"
    logger.info(f"Loading data from {data_path}...")
    try:
        # df = pd.read_csv(config.DATA_PATH)
        df = pd.read_csv(data_path)
        logger.info(f"Successfully loaded {len(df)} samples from dataset")
    except FileNotFoundError:
        logger.error(f"Data file not found at '{data_path}'.")
        logger.error("Please update the path in this script or in config.py.")
        return

    # Log label distribution
    logger.info("Label distribution in dataset:")
    label_counts = df['label'].value_counts()
    for label, count in label_counts.items():
        logger.info(f"  {label}: {count} samples ({count/len(df)*100:.1f}%)")

    # 2. Split Data
    # We use the same split parameters as train.py to ensure the test set is identical.
    logger.info("Splitting data into training and test sets...")
    train_df, test_df = train_test_split(
        df,
        test_size=config.TEST_SPLIT_SIZE,
        random_state=42, # Use same random state for consistency
        stratify=df['label']
    )
    logger.info(f"Data split complete:")
    logger.info(f"  Training samples: {len(train_df)}")
    logger.info(f"  Test samples: {len(test_df)}")

    X_train = train_df['text']
    y_train = train_df['label']
    X_test = test_df['text']
    y_test = test_df['label']

    # 3. Feature Engineering (TF-IDF)
    logger.info("Creating TF-IDF features...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    
    logger.info("Fitting vectorizer on training data...")
    X_train_tfidf = vectorizer.fit_transform(X_train)
    
    logger.info("Transforming test data...")
    X_test_tfidf = vectorizer.transform(X_test)
    logger.info(f"TF-IDF matrix shape (train): {X_train_tfidf.shape}")

    # 4. Model Training
    logger.info("Training Logistic Regression model...")
    # Using class_weight='balanced' to counteract the class imbalance
    model = LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)
    model.fit(X_train_tfidf, y_train)
    logger.info("Model training complete.")

    # 5. Evaluation
    logger.info("Evaluating model on the test set...")
    y_pred = model.predict(X_test_tfidf)
    
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=config.LABEL_MAP.keys())
    cm = confusion_matrix(y_test, y_pred)

    logger.info("\n--- Baseline Model Evaluation Results ---")
    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:\n" + report)
    logger.info("\nConfusion Matrix:\n" + str(cm))
    logger.info("-----------------------------------------")

    # 6. Save Model and Vectorizer
    logger.info(f"Saving model and vectorizer to {BASELINE_MODEL_SAVE_PATH}...")
    joblib.dump(model, BASELINE_MODEL_SAVE_PATH / "logistic_regression_model.joblib")
    joblib.dump(vectorizer, BASELINE_MODEL_SAVE_PATH / "tfidf_vectorizer.joblib")
    logger.info("Baseline model artifacts saved successfully.")
    logger.info("Baseline training pipeline completed!")


if __name__ == "__main__":
    main()
