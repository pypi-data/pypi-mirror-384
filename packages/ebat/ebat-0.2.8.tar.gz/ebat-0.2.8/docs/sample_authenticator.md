# BaseClassifier

## Overview

The BaseClassifier class serves as an abstract base class for all classification models. It defines the interface for
identification, verification, and authentication methods. This class can be used as a starting point when developing a
new authentication system evaluated with EBAT.

## Methods

### identification

Abstract Method Performs identification on the given input data X_test.

### verification

Abstract Method Performs verification on the given input data X_test.

### authentication

Abstract Method Performs authentication on the given input data X_auth.

# MLPModel

## Overview

The MLPModel class represents a simple multi-layer perceptron (MLP) model implemented using PyTorch.

## Methods

### \__init__

Initializes the MLP model with the specified number of input nodes, output nodes, and middle layer size.

### forward

Defines the forward pass through the network, applying linear transformations, ReLU activation, dropout, and softmax
output.

# SimpleMLP

## Overview

The SimpleMLP class is a concrete implementation of the BaseClassifier interface, using an MLP model for classification.
It can be used as a starting point for development of a more complex system with EBAT capabilities. It is also used as a
demo class in this file.

## Methods

### \__init__

Initializes the SimpleMLP classifier with the specified input nodes, output nodes, and middle layer size. Sets up the
device, model, optimizer, and loss function.

### training

Trains the classifier on the given training data using the Adam optimizer and the specified loss function.

### identification

Performs identification on the given input data X_id using the trained model.

### verification

Performs verification on the given input data X_ver using the trained model.

### authentication

Performs authentication on the given input data X_auth using the trained model, returning the maximum user probability
as the probability of successful authentication.

# Example Usage

```python
data_supplier = MedbaSupplier({})
data_supplier.load_datasets()

# Create a SimpleMLP classifier
classifier = SimpleMLP(input_nodes=36, output_nodes=3, middle_layer_size=2048)

# Train the classifier
train, _, test, _ = data_supplier.fetch_and_split_identification()
classifier.training(train)

# Generate identification predictions
id_pred = classifier.identification(test)

# Generate verification predictions per user
for i in range(data_supplier.config["user_num"]):
    ver_train, _, ver_test, ver_adver = data_supplier.fetch_and_split_verification(i)
    verifier = SimpleMLP(input_nodes=36, output_nodes=2, middle_layer_size=2048)
    verifier.training(ver_train)
    verifier.verification(ver_adver)

# Generate authentication predictions
_, _, _, adver_data = data_supplier.fetch_and_split_authentication()
auth_pred = classifier.authentication(auth_data)

```
