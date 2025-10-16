# Pabulib (.pb) format file: Checker

A Python library for validating files in the .pb (Pabulib) format, ensuring compliance with the standards described at pabulib.org/format.

```
pip install git+https://github.com/pabulib/checker.git
```

### TODO
1. pycountry should be installed
2. tests should be run before deployment - CI/CD (ATM manually via command `pytest tests`)


## Overview
The `Checker` is a utility for processing and validating `.pb` files. It performs a wide range of checks to ensure data consistency across `meta`, `projects`, and `votes` sections. We are very open for any code suggestions / changes.

---

## Features
### Key Functions
- **Budget Validation:** Ensures that project costs align with the defined budget and checks for overages.
- **Vote and Project Count Validation:** Cross-verifies counts in metadata against actual data.
- **Vote Length Validation:** Validates that each voter’s submissions comply with minimum and maximum limits.
- **Duplicate Votes Detection:** Identifies repeated votes within individual submissions.
- **Project Selection Validation:** Ensures compliance with defined selection rules, such as Poznań or greedy algorithms.
- **Field Structure Validation:** Verifies field presence, order, types, and constraints in metadata, projects, and votes.
- **Date Range Validation:** Checks that metadata contains a valid date range.

---

## Results Structure
The results from the validation process include three main sections:

### 1. **Metadata**
Tracks the overall processing statistics:
- `processed`: Total number of files processed.
- `valid`: Count of valid files.
- `invalid`: Count of invalid files.

### 2. **Summary**
Provides aggregated error and warning counts by type for all processed files. Example:
```json
{
  "empty lines": 3,
  "comma in float!": 2,
  "budget exceeded": 1
}
```

### 3. **File Results**
Details the outcomes for each processed file. Includes:
- `webpage_name`: Generated name based on metadata.
- `results`:
  - `File looks correct!` if no errors or warnings.
  - Detailed errors and warnings if issues are found.

### Example Output
#### Valid File
```json
{
  "metadata": {
    "processed": 1,
    "valid": 1,
    "invalid": 0
  },
  "summary": {},
  "file1": {
    "webpage_name": "Country_Unit_Instance_Subunit",
    "results": "File looks correct!"
  }
}
```

#### Invalid File
```json
{
  "metadata": {
    "processed": 1,
    "valid": 0,
    "invalid": 1
  },
  "summary": {
    "empty lines": 1,
    "comma in float!": 1
  },
  "file1": {
    "webpage_name": "Country_Unit_Instance_Subunit",
    "results": {
      "errors": {
        "empty lines": {
          1: "contains empty lines at: [10, 20]"
        },
        "comma in float!": {
          1: "in budget"
        }
      },
      "warnings": {
        "wrong projects fields order": {
          1: "projects wrong fields order: ['cost', 'name', 'selected']."
        }
      }
    }
  }
}
```

---

## Possible Issues
### Errors
Critical issues that need to be fixed:
- **Empty Lines:** `contains empty lines at: [line_numbers]`
- **Comma in Float:** `comma in float value at {field}`
- **Project with No Cost:** `project: {project_id} has no cost!`
- **Single Project Exceeded Whole Budget:** `project {project_id} has exceeded the whole budget!`
- **Budget Exceeded:** `Budget exceeded by selected projects`
- **Fully Funded Flag Discrepancy:** `fully_funded flag different than 1!`
- **Unused Budget:** `Unused budget could fund project: {project_id}`
- **Different Number of Votes:** `votes number in META: {meta_votes} vs counted from file: {file_votes}`
- **Different Number of Projects:** `projects number in META: {meta_projects} vs counted from file: {file_projects}`
- **Vote with Duplicated Projects:** `duplicated projects in a vote: {voter_id}`
- **Vote Length Exceeded:** `Voter ID: {voter_id}, max vote length exceeded`
- **Vote Length Too Short:** `Voter ID: {voter_id}, min vote length not met`
- **Different Values in Votes:** `file votes vs counted votes mismatch for project: {project_id}`
- **Different Values in Scores:** `file scores vs counted scores mismatch for project: {project_id}`
- **No Votes or Scores in Projects:** `No votes or scores found in PROJECTS section`
- **Invalid Field Value:** `field '{field_name}' has invalid value`

### Warnings
Non-critical issues that should be reviewed:
- **Wrong Field Order:** `{section_name} contains fields in wrong order: {fields_list}`
- **Poznań Rule Not Followed:** `Projects not selected but should be: {project_ids}`
- **Greedy Rule Not Followed:** `Projects selected but should not: {project_ids}`

---

## How to Use
### Installation
1. Ensure all dependencies are installed:
   - Python 3.8+
   - Required modules: 
        - `pycountry`
    ```bash
    pip install -r requirements.txt
    ```
   
   Install as a python package directly from github:
    ```
    pip install git+https://github.com/pabulib/checker.git
    ```

### To reinstall it (to get newest pushed code)
```bash
pip uninstall -y pabulib 
pip install git+https://github.com/pabulib/checker.git
```


### Usage
1. **Import the `Checker` class:**
    ```python
    from pabulib.checker import Checker
    ```

2. **Instantiate the `Checker` class:**
   ```python
   checker = Checker()
   ```

3. **Process Files:**
You can use `process_files` method which takes a list of path to files or their contents.
   ```python
   files = ["path/to/file1.pb", "raw content of file2"]
   results = checker.process_files(files)
   ```

4. **Get the results:** ATM results is a python dict
    ```python
    import json

    # for a summary, errors accross all files
    print(json.dumps(results["summary"], indent=4))

    # processing metadata, how many files were processed etc
    print(json.dumps(results["metadata"], indent=4)) 


    print(results) # to get details.
    # for example
    print(results[<file_name>])
    ```

---

### Running Example Files

You can process example `.pb` files using the script `examples/run_examples.py`. This script demonstrates how to use the `Checker` to validate files.

1. Example files are located in the `examples/` directory:
   - `example_valid.pb`: A valid `.pb` file.
   - `example_invalid.pb`: A `.pb` file containing errors.

2. Run the script:

```bash
python examples/run_examples.py
```

3. The results for both valid and invalid files will be printed in JSON format.

---

## Customization
To add new validation rules or checks:
1. Define a new method in the `Checker` class.
2. Integrate it into the `run_checks` method for sequential execution.

---

## Additional Information
For detailed examples or advanced usage, refer to the comments in the source code.

