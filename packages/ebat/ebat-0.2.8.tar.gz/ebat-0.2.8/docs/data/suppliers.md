# EbatDataset

## Overview

The EbatDataset class represents a dataset for behavioral biometrics, containing input data X and corresponding labels
y. It is extended from torch.utils.data and behaves as any other PyTorch Dataset. All EBAT suppliers should supply
datasets as EbatDataset-s.

# Supplier

## Overview

The Supplier class serves as an abstract base class for data suppliers, providing a common interface for loading and
splitting datasets. This class should be extended when integrating new datasets into EBAT.

## Methods

### load_datasets

Abstract Method Loads the datasets according to the given configuration. Must be implemented by child classes. The split
between train, validation, testing, and adversarial datasets is dataset-dependent. Nevertheless, it should follow
standard machine learning practices to prevent data leakage. Furthermore, the testing and adversarial parts should come
from different users that performed experiments under equivalent conditions.

### fetch_and_split_identification

Returns the training, validation, test, and adversarial datasets for identification. The four sets here are identical to
the data loaded by _load_datasets_ method.

### fetch_and_split_verification

Returns the training, validation, test, and adversarial datasets for verification, with the specified authentication
user. The four sets are balanced between the positive (auth\_user) and negative (everyone else) class.

### fetch_and_split_authentication

Returns the training, validation, test, and adversarial datasets for authentication. First three sets are identical to
the _fetch\_and\_split\_identification_. Adversarial set however, consists of both testing and adversarial datasets,
where the two are merged and relabelled with a new binary ground truth — legitimate or adversarial data.

### fetch_and_split_session_takeover_attack

It works with identification, verification, and authentication and returns the same training, validation, and
adversarial datasets. The testing dataset instead consists of a single session takeover attack data. The attack itself
is constructed from a first half of a testing session of one of the legitimate users and a second half of testing
session data from one of the attackers.

# MedbaSupplier

## Overview

The MedbaSupplier class is a concrete implementation of the Supplier interface, providing datasets from the Medba
data collection. We collected this dataset by ourselves as a part of our previous efforts, therefore, it downloads
automatically if EBAT does not detect it in the appropriate directory. For more information
visit: https://www.sciencedirect.com/science/article/pii/S2352340924006644

## Configuration

| Parameter    | Description                                                                                                                                                                     | Valid Values                                                                                | Default Value                                            |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|----------------------------------------------------------|
| seed         | Set a random seed                                                                                                                                                               | integer                                                                                     | 42                                                       |
| verbose      | Set the verbosity of the supplier                                                                                                                                               | 0, 1, 2                                                                                     | 0                                                        |
| user\_num    | Number of legitimate users randomly selected by EBAT. Overwritten by _users_.                                                                                                   | 2-27                                                                                        | 15                                                       |
| users        | Determined list of legitimate users.                                                                                                                                            | List of integer indices of selected users.                                                  | Random user\_num number of users.                        |
| adv\_users   | Determined list of adversarial users.                                                                                                                                           | List of integer indices of selected adversarial users.                                      | Random user\_num number of users different from _users_. |
| scale        | Scale the data with sklearn's _MinMaxScaler_.                                                                                                                                   | boolean                                                                                     | True                                                     |
| lookback     | Construct a tensor with dimensions (lookback, n\_samples, n\_features). Used when input needs to be a sequence of data (e.g. with RNNs). If set to 0, no lookback is generated. | integer                                                                                     | 0                                                        |
| window       | Width of the sliding window to process the data in seconds. If set to 0, no sliding window is applied.                                                                          | float                                                                                       | 1.0                                                      | 
| window\_step | Stride of the sliding window in seconds.                                                                                                                                        | float                                                                                       | 0.5                                                      |
| task         | Select the experimental task.                                                                                                                                                   | One of: "Hidden Patterns", "Number Comparison", "Treasure Hunt", "Typing".                  | "Number Comparison"                                      |
| exp\_device  | Select the experimental device.                                                                                                                                                 | One of: "comp", "tab".                                                                      | "comp"                                                   |
| train        | Select the training difficulty and session.                                                                                                                                     | Dictionary of two keys with integer values. 0, 1, or 2 for "diff", and 0, or 1 for session. | {"diff": 0, "session": 0}                                |
| valid        | Select the validation difficulty and session.                                                                                                                                   | Dictionary of two keys with integer values. 0, 1, or 2 for "diff", and 0, or 1 for session. | {"diff": 1, "session": 1}                                |
| test         | Select the testing difficulty and session.                                                                                                                                      | Dictionary of two keys with integer values. 0, 1, or 2 for "diff", and 0, or 1 for session. | {"diff": 2, "session": 1}                                |
| iot\_data    | Include sensor data from IMUs and force sensors.                                                                                                                                | boolean                                                                                     | True                                                     | 
| radar\_data  | Include short mmWave radar data.                                                                                                                                                | boolean                                                                                     | False                                                    |

## Datasets Shape

The supplied datasets come in different shapes, depending on several configuration parameters. _N_ represents the number
of samples in the dataset:

| user\_num | lookback | iot\_data | radar\_data | Input shape  | Label shape |
|-----------|----------|-----------|-------------|--------------|-------------|
| U         | 0        | True      | False       | (_N_, 28)    | (_N_, U)    |
| U         | L        | True      | False       | (_N_, L, 28) | (_N_, U)    |
| U         | 0        | False     | True        | (_N_, 11)    | (_N_, U)    |
| U         | L        | False     | True        | (_N_, L, 11) | (_N_, U)    |
| U         | 0        | True      | True        | (_N_, 39)    | (_N_, U)    |
| U         | L        | True      | True        | (_N_, L, 39) | (_N_, U)    |

# HmogSupplier

## Overview

The HmogSupplier class is a concrete implementation of the Supplier interface, providing datasets for the HMOG data
collection. For more information and to download the data collection, visit: https://hmog-dataset.github.io/hmog/

## Configuration

| Parameter    | Description                                                                                                                                                                     | Valid Values                                                                             | Default Value                                            |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|----------------------------------------------------------|
| seed         | Set a random seed                                                                                                                                                               | integer                                                                                  | 42                                                       |
| verbose      | Set the verbosity of the supplier                                                                                                                                               | 0, 1, 2                                                                                  | 0                                                        |
| user\_num    | Number of legitimate users randomly selected by EBAT. Overwritten by _users_.                                                                                                   | 2-27                                                                                     | 15                                                       |
| users        | Determined list of legitimate users.                                                                                                                                            | List of integer indices of selected users.                                               | Random user\_num number of users.                        |
| adv\_users   | Determined list of adversarial users.                                                                                                                                           | List of integer indices of selected adversarial users.                                   | Random user\_num number of users different from _users_. |
| scale        | Scale the data with sklearn's _MinMaxScaler_.                                                                                                                                   | boolean                                                                                  | True                                                     |
| lookback     | Construct a tensor with dimensions (lookback, n\_samples, n\_features). Used when input needs to be a sequence of data (e.g. with RNNs). If set to 0, no lookback is generated. | integer                                                                                  | 0                                                        |
| window       | Width of the sliding window to process the data in seconds. If set to 0, no sliding window is applied.                                                                          | float                                                                                    | 1.0                                                      | 
| window\_step | Stride of the sliding window in seconds.                                                                                                                                        | float                                                                                    | 0.5                                                      |
| task         | Select the experimental task.                                                                                                                                                   | One of: "read\_sit", "read\_walk", "write\_sit", "write\_walk", "map\_sit", "map\_walk". | "read\_sit"                                              |
| train        | Select the training session.                                                                                                                                                    | Dictionary of a single key with integer values. 0, 1, or 2 for "session".                | {"session": 0}                                           |
| valid        | Select the validation session.                                                                                                                                                  | Dictionary of a single key with integer values. 0, 1, or 2 for "session".                | {"session": 1}                                           |
| test         | Select the testing session.                                                                                                                                                     | Dictionary of a single key with integer values. 0, 1, or 2 for "session".                | {"session": 2}                                           |

## Datasets Shape

The supplied datasets come in different shapes, depending on several configuration parameters. _N_ represents the number
of samples in the dataset:

| user\_num | lookback | Input shape | Label shape |
|-----------|----------|-------------|-------------|
| U         | 0        | (_N_, 9)    | (_N_, U)    |
| U         | L        | (_N_, L, 9) | (_N_, U)    |

# UciharSupplier

## Overview

The UciharSupplier class is a concrete implementation of the Supplier interface, providing datasets for the UCI HAR
data collection. For more information and to download the data collection,
visit: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones

## Configuration

| Parameter    | Description                                                                                                                                                                     | Valid Values                                           | Default Value                                            |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|----------------------------------------------------------|
| seed         | Set a random seed                                                                                                                                                               | integer                                                | 42                                                       |
| verbose      | Set the verbosity of the supplier                                                                                                                                               | 0, 1, 2                                                | 0                                                        |
| user\_num    | Number of legitimate users randomly selected by EBAT. Overwritten by _users_.                                                                                                   | 2-27                                                   | 15                                                       |
| users        | Determined list of legitimate users.                                                                                                                                            | List of integer indices of selected users.             | Random user\_num number of users.                        |
| adv\_users   | Determined list of adversarial users.                                                                                                                                           | List of integer indices of selected adversarial users. | Random user\_num number of users different from _users_. |
| scale        | Scale the data with sklearn's _MinMaxScaler_.                                                                                                                                   | boolean                                                | True                                                     |
| lookback     | Construct a tensor with dimensions (lookback, n\_samples, n\_features). Used when input needs to be a sequence of data (e.g. with RNNs). If set to 0, no lookback is generated. | integer                                                | 0                                                        |
| window       | Width of the sliding window to process the data in seconds. If set to 0, no sliding window is applied.                                                                          | float                                                  | 1.0                                                      | 
| window\_step | Stride of the sliding window in seconds.                                                                                                                                        | float                                                  | 0.5                                                      |

## Datasets Shape

The supplied datasets come in different shapes, depending on several configuration parameters. _N_ represents the number
of samples in the dataset:

| user\_num | lookback | Input shape   | Label shape |
|-----------|----------|---------------|-------------|
| U         | 0        | (_N_, 561)    | (_N_, U)    |
| U         | L        | (_N_, L, 561) | (_N_, U)    |

# ResGaitSupplier

## Overview

The ResGaitSupplier class is a concrete implementation of the Supplier interface, providing datasets for the ReSGait
data collection. For more information and to download the data collection,
visit: https://faculty.sustech.edu.cn/?cat=3&tagid=yusq&orderby=date&iscss=1&snapid=1&go=2&lang=en

## Configuration

| Parameter  | Description                                                                                                                                                                     | Valid Values                                                              | Default Value                                            |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|----------------------------------------------------------|
| seed       | Set a random seed                                                                                                                                                               | integer                                                                   | 42                                                       |
| verbose    | Set the verbosity of the supplier                                                                                                                                               | 0, 1, 2                                                                   | 0                                                        |
| user\_num  | Number of legitimate users randomly selected by EBAT. Overwritten by _users_.                                                                                                   | 2-86                                                                      | 15                                                       |
| users      | Determined list of legitimate users.                                                                                                                                            | List of integer indices of selected users.                                | Random user\_num number of users.                        |
| adv\_users | Determined list of adversarial users.                                                                                                                                           | List of integer indices of selected adversarial users.                    | Random user\_num number of users different from _users_. |
| lookback   | Construct a tensor with dimensions (lookback, n\_samples, n\_features). Used when input needs to be a sequence of data (e.g. with RNNs). If set to 0, no lookback is generated. | integer                                                                   | 0                                                        |
| mode       | Select if we want to retrieve the pose or the silhouette dataset.                                                                                                               | One of: "pose", "silhouette".                                             | "pose"                                                   |
| train      | Select the training session.                                                                                                                                                    | Dictionary of a single key with integer values. 0, 1, or 2 for "session". | {"session": 0}                                           |
| valid      | Select the validation session.                                                                                                                                                  | Dictionary of a single key with integer values. 0, 1, or 2 for "session". | {"session": 1}                                           |
| test       | Select the testing session.                                                                                                                                                     | Dictionary of a single key with integer values. 0, 1, or 2 for "session". | {"session": 2}                                           |

## Datasets Shape

The supplied datasets come in different shapes, depending on several configuration parameters. _N_ represents the number
of samples in the dataset:

| user\_num | lookback | mode         | Input shape        | Label shape |
|-----------|----------|--------------|--------------------|-------------|
| U         | 0        | "pose"       | (_N_, 36)          | (_N_, U)    |
| U         | L        | "pose"       | (_N_, L, 36)       | (_N_, U)    |
| U         | 0        | "silhouette" | (_N_, 224, 224)    | (_N_, U)    |
| U         | L        | "silhouette" | (_N_, L, 224, 224) | (_N_, U)    |

# LibriSpeechSupplier

## Overview

The LibriSpeechSupplier class is a concrete implementation of the Supplier interface, providing datasets for the
LibriSpeech
data collection. For more information and to download the data collection,
visit: https://www.openslr.org/12

## Configuration

| Parameter  | Description                                                                                                                                                                     | Valid Values                                                              | Default Value                                            |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|----------------------------------------------------------|
| seed       | Set a random seed                                                                                                                                                               | integer                                                                   | 42                                                       |
| verbose    | Set the verbosity of the supplier                                                                                                                                               | 0, 1, 2                                                                   | 0                                                        |
| user\_num  | Number of legitimate users randomly selected by EBAT. Overwritten by _users_.                                                                                                   | 2-54                                                                      | 15                                                       |
| users      | Determined list of legitimate users.                                                                                                                                            | List of integer indices of selected users.                                | Random user\_num number of users.                        |
| adv\_users | Determined list of adversarial users.                                                                                                                                           | List of integer indices of selected adversarial users.                    | Random user\_num number of users different from _users_. |
| lookback   | Construct a tensor with dimensions (lookback, n\_samples, n\_features). Used when input needs to be a sequence of data (e.g. with RNNs). If set to 0, no lookback is generated. | integer                                                                   | 0                                                        |
| mode       | Select if we want to generate MFCCs or the spectrogram.                                                                                                                         | One of: "mfcc", "spectrogram".                                            | "mfcc"                                                   |
| mfcc\_n    | If _mode_ "mfcc" is selected, _mfcc\_n_ sets the number of MFCCs generated.                                                                                                     | integer                                                                   | 32                                                       |
| train      | Select the training session.                                                                                                                                                    | Dictionary of a single key with integer values. 0, 1, or 2 for "session". | {"session": 0}                                           |
| valid      | Select the validation session.                                                                                                                                                  | Dictionary of a single key with integer values. 0, 1, or 2 for "session". | {"session": 1}                                           |
| test       | Select the testing session.                                                                                                                                                     | Dictionary of a single key with integer values. 0, 1, or 2 for "session". | {"session": 2}                                           |

## Datasets Shape

The supplied datasets come in different shapes, depending on several configuration parameters. _N_ represents the number
of samples in the dataset:

| user\_num | lookback | mode          | mfcc\_n | Input shape    | Label shape |
|-----------|----------|---------------|---------|----------------|-------------|
| U         | 0        | "mfcc"        | M       | (_N_, M)       | (_N_, U)    |
| U         | L        | "mfcc"        | M       | (_N_, L, M)    | (_N_, U)    |
| U         | 0        | "spectrogram" | n.a.    | (_N_, 1025)    | (_N_, U)    |
| U         | L        | "spectrogram" | n.a.    | (_N_, L, 1025) | (_N_, U)    |

# Example Usage

```python
# Create a supplier class with the configuration dictionary.
sup = MedbaSupplier({"user_num": 15, "verbose": 2})

# Load the datasets internally.
sup.load_datasets()

# Fetch the identification datasets. The adversarial dataset is not needed for identification.
train, valid, test, _ = sup.fetch_and_split_identification()

# Fetch the verification datasets for user with id 42.
train, valid, test, adver = sup.fetch_and_split_verification(42)

# Fetch the authentication datasets.
train, valid, test, adver = sup.fetch_and_split_authentication()
```

# Adding a New Supplier

To include a new dataset extend the Supplier base class by following the steps below. Follow the form put in place by
already included dataset supplier classes:

1. Define the new children class that inherits from the `Supplier` base class.
2. Implement the `load_datasets` method to load the datasets according to the given configuration.
3. Initialize class-specific attributes in the `__init__` method.
4. Implement the `_check_if_downloaded` method to check if the dataset is downloaded, provide guidance on doing so, and
   extract downloaded files.

# Adding a New Threat Model

As definitions of threat models vary, so do the implementation requirements. Following the session takeover attack
mould, adding a new threat model should consist of two steps:

1. Implement a new method in the `Supplier` base class that constructs the data according to the threat model
   definition.
2. Implement a new evaluation function in the `evaluator.py` file to scrutinise against the given threat model.
