# **Adobe India Hackathon 2025: PDF Processing Solution**

## **Overview**

This project is a solution for Challenge 1a, which requires implementing a PDF processing system to extract structured data (title and outline) from PDF documents and output the results as JSON files.

The solution is fully containerized using Docker and is designed to meet the critical performance and resource constraints of the challenge, including no network access during runtime.

## **Solution Architecture: Feature Engineering & Classical ML**

This solution uses a locally-trained Machine Learning model based on a **Random Forest Classifier**. This approach was chosen for its high accuracy and efficiency on small, specific datasets, making it ideal for the challenge constraints.

Instead of relying on large, data-hungry deep learning models, this solution uses intelligent **feature engineering**. The model analyzes various structural and stylistic characteristics of each line of text within a PDF to determine its role in the document.

The key features extracted for each line include:

* **Font Size:** The absolute size of the text (e.g., 24pt).  
* **Relative Font Size:** How the font size of a line compares to the average font size on that specific page. This is a powerful indicator of importance.  
* **Font Style:** Whether the text is **bold**.  
* **Positional Data:** If a line is located in the top 15% of the page, which is common for titles and major headers.  
* **Textual Features:** Basic characteristics like line length, word count, and whether the text is in ALL CAPS.

By training on these rich, language-independent features, the model learns to classify each line as a TITLE, a header (H1, H2, etc.), or regular TEXT. This allows it to accurately reconstruct the document's structure without needing thousands of training examples. The data preparation is fully automated, using a robust multi-stage matching algorithm to create a high-quality training set from the provided PDFs and JSONs.

## **Libraries and Models**

This solution exclusively uses open-source libraries and a lightweight, locally-trained model.

### **Key Technologies**

* **scikit-learn**: The core machine learning library used for the RandomForestClassifier model. It is fast, efficient, and perfect for this classification task.  
* **pdfplumber**: A powerful, best-in-class library for extracting detailed information from PDFs, including text, font metadata (size, name), and positional coordinates.  
* **thefuzz**: A library used during the automated data preparation phase to robustly match extracted text with ground-truth labels using fuzzy string matching, overcoming minor text extraction inconsistencies.

The trained model (doc\_classifier.pkl) is a lightweight pickle file, which is significantly smaller than the 200MB size limit.

## **How to Build and Run**

### **Prerequisites**

* Docker installed and running.

### **1\. Build the Docker Image**

Navigate to the project's root directory (where the Dockerfile is located) and run the build command.

docker build \--platform linux/amd64 \-t pdf-processor .

### **2\. Run the Container**

Create input and output directories in your project root. Place the PDFs you want to process into the input folder. Then, run the container with the following command:

docker run \--rm \-v $(pwd)/input:/app/input:ro \-v $(pwd)/output:/app/output \--network none pdf-processor

* \-v $(pwd)/input:/app/input:ro: Mounts your local input folder as a read-only volume inside the container.  
* \-v $(pwd)/output:/app/output: Mounts your local output folder where the resulting JSON files will be saved.  
* \--network none: Ensures no internet access during runtime, as per the challenge rules.

The container will automatically process all PDFs in the input directory and save the corresponding JSON files to your output directory.
