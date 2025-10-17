<a href="https://github.com/arjunroyihrpa/MMM_fair">
  <img src="https://raw.githubusercontent.com/arjunroyihrpa/MMM_fair/main/images/mmm-fair.png" alt="MMM-Fair Logo" width="200"/>
</a>

# MMM-Fair-CLI

[![PyPI](https://img.shields.io/pypi/v/mmm-fair-cli)](https://pypi.org/project/mmm-fair-cli/)
[![License](https://img.shields.io/github/license/arjunroyihrpa/MMM_fair)](https://github.com/arjunroyihrpa/MMM_fair/blob/main/LICENSE)



**MMM-Fair-CLI** is a lightweight, command-line-only version of the [MMM-Fair framework](https://github.com/arjunroyihrpa/MMM_fair) for fairness-aware boosting. It excludes the web UI, LLMs, and chat features.

---

## 🔧 Installation

```bash
pip install mmm-fair-cli
```

Requires Python 3.12+.

Dependencies: numpy, scikit-learn, tqdm, pymoo, pandas, ucimlrepo, skl2onnx, etc.

---
## 🚀 Quick Usage (CLI)

```bash
python -m mmm_fair_cli.train_and_deploy \
  --classifier MMM_Fair_GBT \
  --dataset mydata.csv \
  --target label_col \
  --prots prot_1 prot_2 \
  --nprotgs npg1 npg2 \
  --constraint DP \
  --early_stop True \
  --n_learners 100 \
  --deploy pickle \
  --moo_vis True
```
### With Known Dataset from Uciml repo

```bash
python -m mmm_fair_cli.train_and_deploy \
  --classifier MMM_Fair_GBT \
  --dataset Adult \
  --prots race sex \
  --nprotgs White Male \
  --constraint EO \
  --deploy onnx \
  --moo_vis True
```
---

### Example Workflow
1.	**Choose** Fairness Constraint: e.g., DP, EO, or EP.
2.	**Define** sensitive attributes in saIndex and the protected-group condition in saValue.
3.	**Pick** base learner (e.g., DecisionTreeClassifier(max_depth=5)) or gradient-based approach.
4.	**Train** with a large number of estimators (n_estimators=300 or max_iter=300).
5.	**Optionally** do partial ensemble selection with update_theta(criteria="all") or update_theta(criteria="fairness") .
6.	**Export** to ONNX or pickle for downstream usage.
7.  **Use** --moo_vis True to open local multi-objective 3D plots for deeper analysis.
8.  **Upload** the .zip file (if exported to onnx) to MAMMOth for bias exploration.

---

#### Note: 
1. Setting --moo_vis True triggers an interactive local HTML page for exploring the multi-objective trade-offs in 3D plots (accuracy vs. class-imbalance vs. fairness, etc.).
2. Currently the fairness intervention only implemented for categorical groups. So if protected attribute is numerical e.g. "age" then for non-protected value i.e. --nprotgs provide a range like 30_60 as argument. 

---

### Additional options

If you want to select the best theta from only the Pareto optimal ensembles set (default is False and selects applies the post-processing to all set of solutions):   

    --pareto True

If you want to provide test data:  

    --test 'your_test_file.csv'
    
Or just test split:  

    --test 0.3
    
If you want change style (default is table, choose from {table, console}) of report displayed ([Check FairBench Library for more details](https://fairbench.readthedocs.io/material/visualization/)):

    --report_type Console

    
**When deploying with 'onnx'**, we change the models to ONNX file(s), and store additional parameters in a model_params.npy. This gets zipped into a .zip archive for distribution/analysis.

---

### MAMMOth Toolkit Integration

For the bias exploration using [MAMMOth](https://mammoth-ai.eu) pipeline it is really important to select 'onnx' as the '--deploy' argument. The [ONNX](https://onnxruntime.ai) model accelerator and model_params.npy are used to integrate with the [MAMMOth-toolkit](https://github.com/mammoth-eu/mammoth-toolkit-releases) or the demonstrator app from the [mammoth-commons](https://github.com/mammoth-eu/mammoth-toolkit-releases) project.
    
## 🐍📓 From Notebook


```python
from mmm_fair import MMM_Fair_GradientBoostedClassifier

clf = MMM_Fair_GradientBoostedClassifier(
    constraint="EO",        # or "DP", "EP"
    alpha=0.1,              # fairness weight
    saIndex=...,            # shape (n_samples, n_protected)
    saValue=...,            # dictionary or None
    max_iter=100,
    random_state=42,
    ## any other arguments that the HistGradientBoostingClassifier from sklearn can handle
)
clf.fit(X, y)
preds = clf.predict(X_test)
```

MMM-Fair includes utility functions to seamlessly work with datasets from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/datasets).

### 🔧 Load a UCI dataset (e.g. Adult dataset)
```python
from mmm_fair import data_uci
from mmm_fair import build_sensitives

# Load dataset with target column
data = data_uci(dataset_name="Adult", target="income")
```
### 🛡️ Define Sensitive Attributes
```python
saIndex, saValue = build_sensitives(
    data.data,
    protected_cols=["race", "sex"],
    non_protected_vals=["White", "Male"]
)
```

---

## 🤖 Need a Web UI or LLM Explanation?

👉 Use the full version:
🔗 [https://pypi.org/project/mmm-fair/](https://pypi.org/project/mmm-fair/)








#### Maintainer: Arjun Roy (arjunroyihrpa@gmail.com)

#### Contributors: Swati Swati (swati17293@gmail.com), Emmanoui Panagiotou (panagiotouemm@gmail.com)

### 🏛️ Funding

MMM-Fair is a research-driven project supported by several public funding initiatives. We gratefully acknowledge the generous support of:

<p align="center">
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://bias-project.org/wp-content/themes/wp-bootstrap-starter/images/Bias_Logo.svg" alt="bias-logo" width="120" />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://mammoth-ai.eu/wp-content/uploads/2022/09/mammoth.svg" alt="mammoth-logo" width="150" style="margin: 0 20px"/>
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <img src="https://stelar-project.eu/wp-content/uploads/2022/08/cropped-stelar-sq.png" alt="stelar-logo" width="100" />
</p>

<p align="center">
  <a href="https://bias-project.org"><strong>Volkswagen Foundation – BIAS</strong></a> &nbsp;&nbsp;&nbsp;
  <a href="https://mammoth-ai.eu"><strong>EU Horizon – MAMMOth</strong></a> &nbsp;&nbsp;&nbsp;
  <a href="https://stelar-project.eu"><strong>EU Horizon – STELAR</strong></a>
</p>


### License & Contributing

This project is released under [Apache License Version 2.0].
Contributions are welcome—please open an issue or pull request on GitHub.

### Contact

For questions or collaborations, please contact [arjun.roy@unibw.de](mailto:arjun.roy@unibw.de) 
Check out the source code at: [GITHUB](https://github.com/arjunroyihrpa/MMM_fair).
