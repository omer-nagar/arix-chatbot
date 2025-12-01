## Step 1: Define Model

Define the model type, architecture, input/output specs, and purpose.

---

### Architecture Mapping (Examples)

| Task Type                 | Architecture              | Example Keyword Cues                        |
|--------------------------|---------------------------|---------------------------------------------|
| `"classification"`       | `"sequence_classification"` | `"classify"`, `"categorize"`, `"detect class"` |
| `"named_entity_recognition"` | `"token_classification"`     | `"detect names"`, `"label words"`, `"NER"`     |
| `"question_answering"`   | `"qa"` or `"extractive_qa"`   | `"answer"`, `"based on passage"`, `"find span"` |
| `"text_generation"`      | `"seq2seq"` or `"decoder"`    | `"generate"`, `"summarize"`, `"rewrite"`        |
| `"text_matching"`        | `"pairwise_classification"` | `"match"`, `"relate"`, `"compare"`             |

---

#### text-type

| Granularity   | Typical Token Count | Best For                                                   |
|---------------|---------------------|-------------------------------------------------------------|
| `phrase`      | 1–10                | Short expressions, sarcasm, entity mentions                |
| `sentence`    | 5–50                | Most classification, NER                                   |
| `paragraph`   | 50–150              | Sentiment with reasoning, multi-sentence relations         |
| `document`    | 150+                | Full-document tasks, summarization, topic modeling         |


### Example Model Specification

```python
MODEL_SPEC = {
    "task_type": "binary_classification",
    "model_purpose": "classify customer reviews as helpful or not",
    "architecture": "sequence_classification",
    "input": {
        "dtype": "string",
        "text-type": "sentence",
        "shape": "-1"
    },
    "output": {
        "dtype": "int",
        "shape": "2"
    },
    # Optional Fields (if needed later):
    "loss_function": "cross_entropy",
    "pretrained_backbone": "bert-base-uncased",
    "metrics": ["accuracy", "f1", "precision", "recall"]
}
```

## Step 2: Define Supporting / Misleading Sub-Features

### 📖 Definitions

#### ✅ Supporting Feature
A **supporting feature** is a signal — such as a token, phrase, or semantic pattern — that **positively contributes to correct predictions** of the main label (e.g., true positives or true negatives). These features are **semantically or contextually aligned** with the ground truth and help the model focus on meaningful input.

> Example: In a medical classification task, terms like *"shortness of breath"* or *"elevated blood pressure"* may support a positive label for a diagnosis.

---

#### ⚠️ Misleading Feature
A **misleading feature** is a signal that **frequently appears in false positives or false negatives**. It correlates **spuriously with the target label** and can lead the model to make incorrect decisions during training or inference.

> Example: In a sentiment classifier, phrases like *"I expected more"* may be mistaken as negative when the full sentence is positive due to sarcasm or contrast.

---

This step defines auxiliary classification sub-tasks that help guide the model during training. These tasks highlight patterns that are either useful (supporting) or harmful (misleading) to the main task.

Each sub-feature is a task with:

- A **name**
- A **description**
- An **explanation** (why it's supporting or misleading)
- A **type**: `"support"` or `"mislead"`
- A set of **classes**
- An **apply_on** field (`"token"` or `"sequence"`)

---

### 🧩 Sub-Feature Definitions (Examples)

| Name                | Type      | Apply On | Classes                             | Description                                     | Explanation                                                                 |
|---------------------|-----------|----------|--------------------------------------|-------------------------------------------------|------------------------------------------------------------------------------|
| `sarcasm_detection` | support   | sequence | `["sarcastic", "not_sarcastic"]`     | Detect whether the input is sarcastic.          | Sarcasm can flip sentiment; detecting it improves contextual understanding. |
| `writing_style`     | mislead   | sequence | `["formal", "informal", "poetic", "neutral"]` | Classify the tone or writing style.            | Some styles falsely correlate with the main label.                          |
| `emotion_type`      | support   | sequence | `["anger", "joy", "neutral", "sadness"]` | Identify the dominant expressed emotion.        | Helps the model connect emotional language to outcomes.                     |
| `negation_presence` | mislead   | token    | `["has_negation", "no_negation"]`    | Detect presence of negation per token.          | Negation can invert meaning and confuse classifiers.                        |
| `domain_specificity`| support   | sequence | `["specific", "generic"]`            | Detect domain-specific language.                | Generic language may not help the task; specific terms often do.           |

---

## 🔄 How to Define Sub-Features

### 📍 If FP / FN Examples Are Available

1. **Collect FP and FN samples** from model predictions.
2. **Inspect patterns** that:
   - Frequently appear in correct predictions → candidate **support** features.
   - Frequently appear in FP or FN → candidate **mislead** features.
3. Label patterns at token or sequence level.
4. Convert them into sub-feature definitions with:
   - Clear class boundaries
   - Apply-on scope (token or sequence)
   - Justified type (`support` or `mislead`)

**Tip**: Use explainability tools like SHAP, LIME, or attention heatmaps to identify influential regions.

---

### 📍 If FP / FN Are NOT Available

1. **Use domain expertise** to hypothesize known helpful/harmful patterns.
2. **Explore unlabeled data** to find recurring patterns (e.g., emotional tone, length, style).
3. Optionally use **LLMs or heuristics** to auto-label:
   - Sarcasm
   - Negation
   - Emotion
   - Writing tone
4. Define sub-feature heads for these tasks and annotate data weakly or semi-automatically.

**Tip**: This is especially useful in early-stage training or low-resource settings.

---

### ✅ Output Specification (for each feature)

```json
{
  "name": "sarcasm_detection",
  "description": "Detect whether the input is sarcastic.",
  "explanation": "Sarcasm flips sentiment and can confuse models without explicit handling.",
  "type": "support",
  "classes": ["sarcastic", "not_sarcastic"],
  "apply_on": "sequence"
}
```

## Step 3: Collect Data

This step is responsible for sourcing and preparing raw data for model training, annotation, and feature extraction.

---

### 📥 Data Sources

1. **Manual Links**
   - Provided URLs or document repositories.
   - Includes websites, datasets, PDFs, or internal sources.

2. **Existing Datasets**
   - Public datasets (e.g., Hugging Face, Kaggle, academic corpora).
   - Internal logs or historical datasets.

3. **Crawled or Scraped Data**
   - Web scraping pipelines tailored to your domain.
   - May require deduplication and cleaning.

---

### 1. **Data Ready for Use**

The data is already segmented, cleaned, and structured. It can be passed directly to downstream stages such as:

- Labeling
- Filtering
- Feature annotation
- Training

#### ✅ Requirements
- Text is already split (e.g., into sentences or paragraphs)
- Each instance has a unique ID
- Token length is known or can be estimated
- Optional metadata is available (e.g., source, domain)

#### 📦 Example Input (Ready)

```json
{
  "id": "doc_001_sent_03",
  "name": "document_001_sent_03",
  "description": "This is the third sentence of document 001.",
  "source": "/link/to/source/document_001",
  "path": "path/to/document_001.csv",
  "state": "ready",
  "text-type": "sentence",
  "metadata": {
    "language": "en",
    "domain": "ecommerce"
  }
}
```

#### 🏷️ Allowed `state` Values

| State         | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| `"raw"`       | Document has been collected but not yet segmented or normalized             |
| `"processed"` | Document has been normalized and cleaned, but not yet split or verified     |
| `"split"`     | Document has been segmented into appropriate text units                     |
| `"ready"`     | Instances are fully ready for filtering, annotation, or training            |
| `"discarded"` | Marked for removal due to low quality, duplication, or irrelevance          |
| `"error"`     | Encountered an error during ingestion or preprocessing                      |

---

### 2. **Raw Data That Needs Processing**

The data consists of large documents or unsegmented text. It must be processed and split based on the model specification — particularly:

- `optimal_length` from `MODEL_SPEC`
- Preferred granularity (sentence, paragraph, etc.)

#### 🧠 Processing Pipeline
- Tokenize the text
- Segment according to max token length and split strategy
- Normalize and tag metadata
- Generate multiple structured instances per document

#### 📦 Example Input (Unprocessed)

```json
{
  "id": "doc_045",
  "name": "document_045",
  "description": "Raw full-text review from e-commerce website.",
  "source": "https://example.com/review/045",
  "path": "raw_data/review_045.txt",
  "state": "raw",
  "text-type": "document",
  "text": "The item arrived late. However, it performed much better than expected. I would buy it again.",
  "metadata": {
    "language": "en",
    "domain": "ecommerce"
  }
}
```

After processing, this single document will be converted into multiple `sentence` or `paragraph` instances with token-aware segmentation.

---

## Optional Step 3.1: Make Data Ready

If your data is in raw form (e.g., full documents, web pages, long reviews), this step helps transform it into clean, structured instances ready for annotation, filtering, or model training.

---

### 🎯 Goal

Transform raw or unstructured text into consistent, well-formed instances with:
- Proper segmentation (sentences, paragraphs, etc.)
- Normalized formatting
- Estimated token lengths
- Clear metadata
- Compatible structure for model training

---

### 🧰 Recommended Tools and Libraries

| Task                          | Tool / Library                              | Notes                                                  |
|-------------------------------|---------------------------------------------|--------------------------------------------------------|
| **Sentence segmentation**     | `spaCy`, `nltk`, `blanchefort/sentence-splitter`, `syntok` | SpaCy is fast and multilingual; syntok preserves punctuation |
| **Token length estimation**   | `transformers` (Tokenizer), `spaCy`         | Use your model's tokenizer to count input tokens       |
| **HTML/text cleaning**        | `beautifulsoup4`, `readability-lxml`, `trafilatura` | Clean boilerplate and extract main content             |
| **PDF/Doc extraction**        | `pdfplumber`, `unstructured`, `textract`    | Handle messy formats like scanned or formatted text    |
| **Language detection**        | `langdetect`, `langid`, `fasttext`          | Filter by supported language                          |
| **Duplication detection**     | `datasketch`, `simhash`, `fuzzywuzzy`       | Identify and remove near-duplicates                   |

---

### ⚙️ Example Processing Pipeline

1. **Load Raw Text**
   - From `.txt`, `.csv`, PDF, scraped HTML, or API source

2. **Clean the Content**
   - Strip tags, extra whitespace, junk characters
   - Extract meaningful text sections

3. **Segment by Granularity**
   - Choose: `"sentence"`, `"paragraph"`, `"phrase"`, `"document"`
   - Use language-aware tokenizer (e.g., `spaCy`) to split

4. **Estimate Token Count**
   - Use the tokenizer from your `MODEL_SPEC` (e.g., `bert-base-uncased`)
   - Optionally filter or split based on `optimal_length`

5. **Attach Metadata**
   - Add `id`, `source`, `domain`, `language`, etc.

6. **Write Structured Output**
   - Store in `.jsonl`, `.csv`, or a unified DB
   - Each row should match the instance format from Step 3

---

### 📦 Example Output Instance (Post-Processing)

```json
{
  "id": "doc_092_sent_001",
  "text": "I love the idea, but the product needs work.",
  "granularity": "sentence",
  "tokens": 14,
  "source": "https://example.com/review/092",
  "path": "raw_data/review_092.html",
  "state": "ready",
  "text-type": "sentence",
  "metadata": {
    "language": "en",
    "domain": "electronics"
  }
}
```


