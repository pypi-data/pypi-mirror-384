# WILDkCAT

[![pypi](https://img.shields.io/pypi/v/wildkcat.svg)](https://pypi.org/project/wildkcat/) [![stable documentation](https://img.shields.io/badge/docs-stable-blue)](https://h-escoffier.github.io/WILDkCAT/)

**WILDkCAT** is a set of scripts designed to extract, retrieve, and predict enzyme turnover numbers (**kcat**) for genome-scale metabolic models.   


> [!WARNING] 
> WILDkCAT is currently in 'beta' version. Some parameters (such as the penalty score) are not yet finalized and some features are still under development.
> Please do not hesitate to try the package, share your experience, and report any issues or suggestions by opening an issue on the [Issues](https://github.com/h-escoffier/WILDkCAT/issues) page.

---

WILDkCAT produces a `.tsv` file with the retrieved and predicted kcat values for each combination of enzyme, substrates in your genome-scale metabolic model.
Each step of the pipeline also generates an HTML report that provides detailed information about the retrieval process to facilitate transparency and reproducibility.
The HTML reports are generated automatically after each stage of the workflow (extractionn, retrieval, prediction) and can be opened directly in any web browser. 

<p align="center"> <img src="docs/report_example.gif" alt="WILDkCAT Report Demo" width="700"/> </p>

[Access the report here](https://h-escoffier.github.io/WILDkCAT/tutorial/general_ecoli_report.html)

## Installation

Install [WILDkCAT](https://pypi.org/project/wildkcat/) directly from PyPI:

```bash
pip install wildkcat
```

## Environment Setup 

Provide your **BRENDA login credentials** and **Entrez API email adress** to query the BRENDA enzyme database and NCBI database.

Create a file named `.env` in the root of your project with the following content:

```bash
ENTREZ_EMAIL=your_registered_email@example.com
BRENDA_EMAIL=your_registered_email@example.com
BRENDA_PASSWORD=your_password
```

> [!IMPORTANT] 
> * Replace the placeholders with the credentials from the account you created on the [BRENDA website](https://www.brenda-enzymes.org).
> * Ensure this file is **not shared publicly** (e.g., add .env to your .gitignore) since it contains sensitive information.
> * The scripts will automatically read these environment variables to authenticate and retrieve kcat values.

---

## Usage

**WILDkCAT** can be used as scripts or via the CLI.

### Command-Line Interface (CLI)

After installation, you can use the WILDkCAT CLI:

```bash
wildkcat --help
```

Example Workflow:

```bash
# Extract kcat data
wildkcat extraction \
    path/to/my_model.json \
    path/to/folder_output

# Retrieve kcat values from databases
wildkcat retrieval \
    path/to/folder_output
    'Organism name' \
    20 30 \  # Temperature range
    6.5 8.5 \  # pH range

# Generate input for CataPro
wildkcat prediction-part1 \
    path/to/folder_output
    6  # Limit matching score 

# Integrate CataPro prediction
wildkcat prediction-part2 \
    path/to/folder_output
    prediction_output.csv \
    6  # Limit matching score

# Generate summary report
wildkcat report \
    path/to/my_model.json \
    path/to/folder_output
```

> [!WARNING]  
> Currently, the [SABIO-RK database](http://sabio.h-its.org) is experiencing server overload and queries can be very slow, especially for large models. In these cases, it is recommended to use only the 'brenda' database in the `retrieval` command.

---

### Programatic Access 

```python
from wildkcat import run_extraction, run_retrieval, run_prediction_part1, run_prediction_part2, generate_summary_report
```

### Example: E. coli Core Model
A ready-to-run example is available [here](https://github.com/h-escoffier/WILDkCAT/blob/main/scripts/run_wildkcat.py). 
It demonstrates a full extraction, retrieval, and prediction workflow on the E. coli core model.

---

## Key scripts 

### `extract_kcat.py`
- Verifies whether the reaction EC number exists.  
- Retains inputs where reaction-associated genes/enzymes are not supported by KEGG.  
- Retains inputs where no enzymes are provided by the model.  
- If multiple enzymes are provided, searches UniProt for catalytic activity.  

---

### `retrieve_kcat.py`
- If the same enzyme is not found, computes identity percentages relative to the identified catalytic enzyme.  
- Applies Arrhenius correction to values within the appropriate pH range.  
- For rows with multiple scores, selects:
  - The best score  
  - The highest identity percentage  
  - The closest organism (if sequence is not available)  
  - The highest kcat value  

---

### `predict_kcat.py`
- If multiple enzymes are provided, searches UniProt for catalytic activity.  
- Skips entries missing KEGG compound IDs.  

--- 

## Feedback & Improvements

Contributions, suggestions, and feedback are very welcome! If you encounter any [issues](https://github.com/h-escoffier/WILDkCAT/issues), have ideas for new features, or notice room for improvement, feel free to open an issue or submit a pull request.