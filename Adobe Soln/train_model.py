import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from joblib import dump

CSV_PATH = "training_data.csv"
MODEL_PATH = "heading_classifier.joblib"

def main():
    df = pd.read_csv(CSV_PATH)
    df = df.dropna()

    X = df[["font_size", "y0", "page_num", "char_len", "word_count", "is_upper", "starts_with_num"]]
    y = df["label"]

    print("📊 Labels:", y.value_counts().to_dict())

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n📈 Classification Report:\n")
    print(classification_report(y_test, y_pred))

    dump(model, MODEL_PATH)
    print(f"✅ Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()
