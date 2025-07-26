import os
import pickle
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline
from features import extract_features
from create_dataset import run_automated_labeling
import traceback

def train_model(data_dir, model_path):
    """
    Automates data creation and trains the Random Forest classifier.
    """
    print("--- Starting Model Training ---")
    
    # 1. Automatically create the labeled dataset from PDFs and JSONs
    print("Step 1: Automatically creating labeled training data...")
    labeled_data_path = os.path.join(data_dir, 'training_data.json')
    training_data = run_automated_labeling(data_dir, labeled_data_path)
    
    if not training_data:
        print("Failed to create training data. Aborting.")
        return

    # 2. Prepare features (X) and labels (y)
    print("\nStep 2: Extracting features and labels...")
    X_dicts = [extract_features(item) for item in training_data]
    y_labels = [item['label'] for item in training_data]

    # 3. Create and train the model pipeline
    print("\nStep 3: Training the Random Forest model...")
    pipeline = make_pipeline(
        DictVectorizer(sparse=False),
        RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    )
    pipeline.fit(X_dicts, y_labels)
    print("Training complete.")

    # 4. Save the trained model
    print("\nStep 4: Saving the model...")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
    print(f"Model saved successfully to {model_path}")

if __name__ == '__main__':
    try:
        train_model('data', 'models/doc_classifier.pkl')
        print("\n--- Training Script Finished Successfully! ---")
    except Exception as e:
        print(f"\n--- AN ERROR OCCURRED: {e} ---")
        traceback.print_exc()
