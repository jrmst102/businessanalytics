# Applied Business Analytics for Marketing Decision-Making  
## Companion Repository for *Business Analytics and Data Visualization*

This repository contains the companion files, datasets, notebooks, and code examples used in **Applied Business Analytics for Marketing Decision-Making**, the course text for **Business Analytics and Data Visualization**.

The course is part of the **MS in Integrated Marketing** at **New York University School of Professional Studies**.

**Instructor:** Dr. Jose Mendoza  
**Title:** Academic Director and Clinical Associate Professor  
**Program:** MS in Integrated Marketing  
**Institution:** New York University, School of Professional Studies  

---

## About This Repository

This repository supports a course and textbook organized around an AI-assisted analytics workflow. Students use Python, Google Colab, Tableau, and AI assistants to prepare data, analyze marketing problems, build preliminary predictive models, create visualizations, and develop managerial recommendations.

The textbook chapters are distributed through the course learning management system. This repository provides the working materials that accompany those chapters, including:

- Python notebooks
- Example datasets
- Code templates
- Verification exercises
- Project starter files
- Visualization support files
- AI-use documentation templates, when applicable

Students should use this repository as a companion resource while working through the weekly chapters.

---

## Textbook

**Mendoza, J. (2026). _Applied Business Analytics for Marketing Decision-Making: Business Analytics and Data Visualization_. Course manuscript, New York University School of Professional Studies.**

The textbook is designed to be used one chapter at a time. Each chapter corresponds to a weekly learning unit and includes a marketing decision context, key concepts, analytics workflow, AI-augmented analytics lab, verification checkpoints, and managerial interpretation activities.

---

## Course Workflow

The course uses a four-part AI-augmented analytics workflow:

### 1. Specify

Before using an AI assistant, define the business question, unit of analysis, variables, method, and success criteria.

### 2. Predict, Then Verify

Before running AI-generated code or accepting AI-generated output, state what you expect the result to show. After running it, check the output against the data, known totals, model metrics, chart logic, or alternative methods.

### 3. Explain

You must be able to explain what every step does and why it matters. This includes code, transformations, models, visualizations, and recommendations.

### 4. Document

Every graded technical submission must include an AI-use record documenting the tools used, key prompts, accepted and rejected outputs, errors encountered, and verification steps performed.

---

## Repository Structure

The repository is organized to support weekly course work.

```text
businessanalytics/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
│
├── notebooks/
│   ├── chapter_01/
│   ├── chapter_02/
│   ├── chapter_03/
│   └── ...
│
├── templates/
│   ├── ai_use_appendix_template.md
│   ├── verification_log_template.md
│   └── project_report_template.md
│
├── tableau/
│   ├── workbooks/
│   └── data/
│
├── projects/
│   ├── project_01_predictive_analytics/
│   └── project_02_data_visualization/
│
├── README.md
└── LICENSE
```

The exact folder structure may evolve as additional chapters, notebooks, and project files are added.

---

## Chapter and File Naming Convention

Files are named to correspond with the textbook chapter sequence.

Examples:

```text
chapter_04_data_preparation.ipynb
chapter_05_descriptive_analytics.ipynb
chapter_07_regression.ipynb
chapter_09_classification.ipynb
chapter_10_forecasting.ipynb
chapter_12_visualization_for_analysis.twbx
```

Students should always use the file associated with the assigned weekly chapter.

---

## Table of Contents Alignment

| Textbook Unit | Topic | Repository Materials |
|---|---|---|
| Chapter 1 | Becoming an AI-Augmented Marketing Analyst | Setup guides, AI-use template |
| Chapter 2 | Marketing Analytics as Decision Support | Specification templates |
| Chapter 3 | Data, Measurement, and Marketing Variables | Data dictionary examples |
| Chapter 4 | Data Preparation and Exploratory Analysis | Colab notebooks, datasets |
| Chapter 5 | Descriptive Analytics and Customer Insight | Summary tables, profiling notebooks |
| Chapter 6 | Segmentation and Targeting Analytics | RFM and clustering notebooks |
| Chapter 7 | Relationships, Drivers, and Regression | Regression notebooks |
| Chapter 8 | Predictive Modeling for Marketing Decisions | Model evaluation notebooks |
| Chapter 9 | Classification, Propensity, and Churn Models | Classification notebooks |
| Chapter 10 | Forecasting Demand, Sales, and Campaign Performance | Forecasting notebooks |
| Chapter 11 | Experiments, A/B Testing, and Causal Evidence | A/B testing notebooks |
| Project #1 | Predictive Analytics Project | Project starter files |
| Chapter 12 | Data Visualization for Analysis | Tableau and visualization files |
| Chapter 13 | Data Visualization for Communication and Decision-Making | Dashboard templates |
| Project #2 | Data Visualization Project | Final project files |

---

## Getting Started

### 1. Clone or Download the Repository

Students may either download the repository as a ZIP file or clone it using Git.

```bash
git clone https://github.com/jrmst102/businessanalytics.git
```

### 2. Open Notebooks in Google Colab

Most Python notebooks are designed to run in Google Colab. To use a notebook:

1. Open the notebook file in GitHub.
2. Download the notebook or open it in Colab.
3. Save a personal copy to your Google Drive.
4. Run the cells in order.
5. Verify the outputs before submitting any work.

### 3. Use the Correct Dataset

Each notebook identifies the dataset required for the exercise. Make sure the dataset path matches the instructions in the notebook or chapter.

### 4. Document AI Use

When using AI tools to generate code, debug errors, interpret output, or draft visualizations, complete the AI-use documentation required for the assignment.

---

## Required Tools

The course uses the following tools:

- **Google Colab** for Python-based analytics
- **Python** for data preparation, exploratory analysis, modeling, and visualization
- **Pandas, NumPy, Matplotlib, scikit-learn, and related libraries** for analytics workflows
- **Tableau Desktop and Tableau Prep** for visual analytics and dashboard development
- **AI assistants** such as ChatGPT, Claude, Gemini, GitHub Copilot, or Colab AI features for code support, explanation, debugging, and visualization prototyping

Tool requirements may vary by chapter or assignment.

---

## Responsible AI Use

AI tools are expected in this course, but they do not replace student responsibility.

You may use AI tools to:

- Generate starter code
- Debug errors
- Explain code or output
- Suggest analytic approaches
- Draft first-pass visualizations
- Improve clarity of written explanations
- Translate technical findings into managerial language

You may not use AI tools to avoid understanding your work.

Submitting AI-generated code, charts, interpretations, or recommendations that you cannot explain or have not verified violates the course AI-use policy. Every technical submission must include the required AI-use documentation.

---

## Verification Expectations

Before submitting any notebook, report, visualization, or project file, check the following:

- Did the code run from beginning to end?
- Are the correct datasets loaded?
- Are the row counts, column names, and data types plausible?
- Are missing values, duplicates, and outliers handled appropriately?
- Do the summary statistics make sense?
- Are model metrics interpreted correctly?
- Are chart scales, labels, and titles accurate?
- Does the managerial recommendation follow from the evidence?
- Is AI use documented clearly?

The goal is not only to produce output. The goal is to produce work that can be explained, defended, and used for decision-making.

---

## Projects

The course includes two major projects.

### Project #1: Predictive Analytics Project

Students apply the analytics methods from the first two parts of the course to a predictive analytics or causal-evidence problem. The project includes business framing, data preparation, model building, validation, managerial recommendation, and an oral defense.

### Project #2: Data Visualization Project

Students create an executive-facing visual report or Tableau dashboard. The project includes a marketing decision context, cleaned data, analytical visualizations, dashboard design, written recommendation, visualization critique, and final presentation.

Project files and templates are available in the `projects/` folder when released.

---

## For Students

Use this repository alongside the assigned weekly chapter.

A recommended workflow:

1. Read the assigned chapter.
2. Open the corresponding notebook or file.
3. Review the business question and data.
4. Specify the analytic task before prompting AI.
5. Run or adapt the code.
6. Verify the output.
7. Interpret the result in managerial language.
8. Complete the assignment and AI-use documentation.

Do not submit repository files without adapting, explaining, and verifying them.

---

## For Instructors

This repository is designed as a companion site for a graduate course in business analytics and data visualization. Materials may be adapted for instructional use with appropriate attribution, subject to the repository license and any dataset-specific restrictions.

---

## Citation

If referencing the course text or repository, use:

```text
Mendoza, J. (2026). Applied Business Analytics for Marketing Decision-Making: Business Analytics and Data Visualization. Course manuscript, New York University School of Professional Studies.
```

Repository:

```text
Mendoza, J. (2026). businessanalytics [GitHub repository]. GitHub. https://github.com/jrmst102/businessanalytics
```

---

## License

This repository currently uses the license included in the `LICENSE` file. Code, notebooks, and instructional support files are governed by that license unless otherwise noted.

Datasets may have separate usage restrictions. Students and instructors should review any dataset-specific notes before redistributing or reusing data outside the course.

The textbook manuscript itself is distributed separately through the course learning management system and is not automatically licensed for public redistribution through this repository.

---

## Contact

**Dr. Jose Mendoza**  
Academic Director and Clinical Associate Professor  
MS in Integrated Marketing  
New York University  
School of Professional Studies  

Course materials and announcements are distributed through Brightspace.
