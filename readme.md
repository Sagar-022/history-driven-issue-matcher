## Past Contribution History as a Key Feature in OSS Issue Recommendation

A pipeline for predicting contributors for an issue in an OSS repository. It computes the similarity between LLM-generated issue skills and contributor skills using TF-IDF, Sentence BERT, and LLM to recommend the most suitable contributors.


## Prerequisites

- Python 3.8+
- Install dependencies:
  ```bash
  pip install torch transformers accelerate sentence-transformers scikit-learn pandas tqdm
- Recommended: Jupyter Notebook or any IDE that supports `.ipynb` and `.py` files


## Hardware Requirements

- Minimum: 24–32 GB VRAM (for full-precision inference)
- Recommended: 40+ GB VRAM (for efficient fp16 or bf16 inference)


## How to Compile and Run

- Open Jupyter Notebook through Anaconda Navigator
  or
  use the following command from terminal:
    ```bash
    jupyter notebook
or
Or use any IDE/tool of your preference (you might need one to run .py files or work via terminal)
- Navigate to Data Mining and Dataset folder in the repo "history-driven-issue-matcher"
- Follow the dataset-miner.md in that folder to generate the main dataset dataset.csv
- Return to the repo root and open main approach.ipynb
- Execute each cell sequentially (e.g., with Shift+Enter)
- All .csv files and evaluation results will be generated automatically
- Then, open "selective skills.ipynb" and execute all cells (just like "main approach.ipynb")


## Output

- dataset.csv                                --> Main dataset
- contributor_skills.csv                     --> All contributors’ skill dataset
- issue_skills.csv                           --> Required skills for solving each issue
- skill_superset.txt                         --> Superset of baseline skills for use in selective skills.ipynb
- selective_contributor_skills.csv           --> Contributors’ skill dataset for selective skills approach
- selective_contributor_skills_filtered.csv  --> Filtered contributor dataset (non-significant contributors removed)
- selective_issue_skills.csv                 --> Issue skill dataset for selective skills approach