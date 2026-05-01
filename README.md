# NCB Employee-Customer Performance Chain

Repository: https://github.com/puppalabejjanapala193-ship-it/ncb-employee-customer-performance-chain

## Overview
This project analyzes how employee perceptions relate to customer outcomes and branch performance at National Choice Bank (NCB). The study tests the employee-customer-performance chain using branch-level survey and operational data.

## Data
- File: NCB_filtered_data_2025-11-26 (2).csv
- Unit of analysis: branch (n = 85)
- Sources (per project documentation): employee surveys, customer evaluations, and operational metrics

## Methods
- Descriptive statistics and correlation analysis
- Regression models (linear and random forest)
- K-means clustering for branch profiles

## Results Snapshot
- Employee index vs service quality: r = 0.164
- Service quality vs loyalty: r = 0.904
- Loyalty models: R^2 = 0.805 to 0.828
- Productivity models: negative R^2

## Repository Structure
- analysis.py: analysis pipeline for models, tables, and figures
- requirements.txt: Python dependencies
- figures/: generated plots and summary tables
- Final_Paper.md: full report
- Final_Paper_updated.docx: formatted Word report (includes repo link)

## Reproducibility
1. Install dependencies:
   - pip install -r requirements.txt
2. Run the analysis:
   - python analysis.py
3. Outputs are written to figures/.

## Notes
All branches in the provided file are labeled Metro, so geographic comparisons are not possible with this dataset.
