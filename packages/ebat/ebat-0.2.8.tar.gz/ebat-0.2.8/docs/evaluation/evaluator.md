# ResultsBase

## Overview

The ResultsBase class serves as an abstract base class for storing and managing evaluation results.

## Methods

### add\_metric

Adds a new metric to the results dictionary.

### save\_results

Saves the results to a JSON file in the results directory.

### retrieve\_results

Retrieves results from a JSON file in the results directory.

# OneoffResults

## Overview

The OneoffResults class represents a set of results for one-off evaluations, such as identification.

## Methods

## metrics

Prints the accuracy, precision, recall, F1 score, and Matthews correlation coefficient.

## visualise

Displays a heatmap of the confusion matrix.

# ContinuousResults

## Overview

The ContinuousResults class represents a set of results for continuous evaluations, such as verification and
authentication.

## Methods

### metrics

Prints the equal error rate and Gini coefficient.

### visualise

Displays several plots:

    Receiver Operating Characteristic (ROC) curve
    Detection Error Tradeoff (DET) curve
    FAR vs. FRR curves
    Frequency count of scores

# Evaluation Metrics

## Overview

The following functions calculate evaluation metrics for identification, verification, and authentication.

## evaluate\_identification

Evaluates an identification model using the provided data and returns a OneoffResults object.

## calculate\_continuous

Calculates continuous evaluation metrics, such as ROC curve, DET curve, and Gini coefficient, and returns a
ContinuousResults object. Called by _evaluate\_verification_ and _evaluate\_identification_.

## evaluate\_verification

Evaluates a verification model using the provided data and returns a ContinuousResults object.

## evaluate\_authentication

Evaluates an authentication model using the provided data and returns a ContinuousResults object.

## compare\_results

Compares the results of multiple approaches by plotting their ROC curves and DET curves.

# Example Usage

```python
data_supplier = MedbaSupplier({})  # create data supplier
data_supplier.load_datasets()  # load data necessary for evaluation

# Evaluate an identification model
id_train, id_valid, id_test, _ = data_supplier.fetch_and_split_identification()  # fetch different parts of the dataset
identifier = ...  # create an identification model with id_train
results = evaluate_identification(identifier, id_test)  # evaluate with testing dataset
results.metrics()
results.visualise()

# Evaluate a verification model for user 42
ver_train, ver_valid, ver_test, ver_adver = data_supplier.fetch_and_split_verification(42)
verifier = ...  # create a verification model with ver_train
results = evaluate_verification(verifier, ver_adver)
results.metrics()
results.visualise()

# Evaluate an authentication model
auth_train, auth_valid, auth_test, auth_adver = data_supplier.fetch_and_split_authentication()
authenticator = ...  # create an authentication model with auth_train
results = evaluate_authentication(authenticator, auth_adver)
results.metrics()
results.visualise()

# Compare results of multiple approaches
approach1 = ...  # create a verification model
approach2 = ...  # create another verification model
results1 = evaluate_verification(approach1, ver_adver)
results2 = evaluate_verification(approach2, ver_adver)
compare_results([results1, results2])
```