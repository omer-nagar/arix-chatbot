
GREETINGS = """
Here’s a cleaned-up, clearer version you can drop in almost as-is, plus a slightly “pro” variant if you want extra structure.

---
**Welcome to Arix — your personal data scientist.**
To set things up properly, answer the questions below as clearly as you can.

1. **What should Arix do with your data?**
   *Describe the main task in plain language.*
   **Examples:**

   * “Classify support tickets into topics (billing, tech issue, sales…).”
   * “Detect pain points and feature requests in customer feedback.”

2. **What kind of input will Arix receive?**
   *Describe the source and format of your data.*
   **Examples:**

   * Short chat messages between users and support agents
   * Transaction records or financial reports (CSV / JSON)

   You can also add: typical length, language (English / multilingual), and whether it’s noisy (typos, slang, etc.).

3. **What should the output look like? (Schema / format)**
   *Describe the exact structure Arix should return.*
   **For Example:**

     ```json
     {
       "sentiment": "negative",
       "feature_requests": [
         {"feature": "top down navigation", "priority": "high", "evidence_span": "I wish there was a way to..."},
         {"feature": "dark mode", "priority": "medium", "evidence_span": "It would be great if..."}
       ]
     }
     ```

---

"""


"""

## Version 2 – “Pro” Onboarding (More Guided)

If you want to make users think a bit more concretely and get better specs from day one:

**Welcome to Arix — your personal data scientist.**
Help Arix understand your use-case by filling out the three fields below.

---

### 1. Task – What do you want Arix to do?

*One clear sentence describing the main goal.*

> “The objective is to …”

**Examples:**

* “…detect and label toxic comments in user chats.”
* “…extract product attributes (size, color, material) from product descriptions.”
* “…identify pain points and feature requests in support tickets.”
* “…classify reviews into sentiment and main topic.”

---

### 2. Input – What data will Arix see?

*Describe the type, source, and typical shape of your input.*

You can mention:

* **Type:** product reviews / chat transcripts / emails / logs / CSV rows / JSON objects
* **Source:** website reviews, Zendesk tickets, CRM notes, internal logs…
* **Typical length:** short snippets (1–2 sentences), paragraphs, full pages
* **Language & style:** English only / multilingual, formal / informal, many typos, etc.

**Example answer:**

> “Short English chat messages between customers and support, 1–3 sentences each, often informal with emojis and typos.”

---

### 3. Output – Exact schema / format you need

*Describe the JSON (or other) structure your system expects.*

**Minimum:**

> “Arix should return a JSON with the following fields…”

Then list fields:

* Field name
* Type (string / boolean / list / object)
* Short description
* Allowed values (if relevant)

**Example:**

```json
{
  "sentiment": "positive | neutral | negative",
  "main_topic": "billing | delivery | product_quality | other",
  "needs_human_review": true,
  "extracted_issues": [
    {
      "issue_type": "delay | refund | damaged_item | other",
      "evidence_span": "exact snippet from the text"
    }
  ]
}
```
"""