import pandas as pd
from sklearn.metrics import cohen_kappa_score

df = pd.read_csv("/workspaces/ERP_Newsletter/data_processed/sample_llm_vs_manual_labels.csv")
subset = df[df['manual_label'].notna()]

agreement = (subset['manual_label'] == subset['llm_label']).mean()
print("Agreement:", round(agreement, 2))

kappa = cohen_kappa_score(subset['manual_label'], subset['llm_label'])
print("Cohen's kappa:", round(kappa, 2))
