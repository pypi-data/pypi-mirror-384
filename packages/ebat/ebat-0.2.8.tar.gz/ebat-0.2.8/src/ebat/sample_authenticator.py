# Copyright (C) 2025 European Union
# This program is free software: you can redistribute it and/or modify
# it under the terms of the EUROPEAN UNION PUBLIC LICENCE v. 1.2 as
# published by the European Union.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# EUROPEAN UNION PUBLIC LICENCE v. 1.2 for further details.

# You should have received a copy of the EUROPEAN UNION PUBLIC LICENCE v. 1.2.
# along with this program.  If not, see <https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12>

from abc import abstractmethod

import numpy as np
import torch
from torch.utils.data import DataLoader

from ebat.data.suppliers import (
    MedbaSupplier,
    HmogSupplier,
    UciharSupplier,
    ResGaitSupplier,
    LibriSpeechSupplier,
)
from ebat.evaluation.evaluator import (
    evaluate_identification,
    evaluate_authentication,
    evaluate_verification,
    compare_results,
    ContinuousResults,
    evaluate_session_takeover_attack,
)


class BaseClassifier:

    def __init__(self):
        self.model = None

    @abstractmethod
    def identification(self, X_test):
        pass

    @abstractmethod
    def verification(self, X_test):
        pass

    @abstractmethod
    def authentication(self, X_auth):
        pass


class MLPModel(torch.nn.Module):
    def __init__(self, input_nodes, output_nodes, middle_layer_size):
        super().__init__()
        self.linear1 = torch.nn.Linear(input_nodes, middle_layer_size)
        self.activation = torch.nn.ReLU()
        self.dropout = torch.nn.Dropout(0.5)
        self.linear2 = torch.nn.Linear(middle_layer_size, output_nodes)
        self.softmax = torch.nn.Softmax(dim=1)

    def forward(self, x):
        x = self.linear1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear2(x)
        x = self.softmax(x)
        return x


class SimpleMLP(BaseClassifier):
    def __init__(self, input_nodes, output_nodes, middle_layer_size=1024):
        super().__init__()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = MLPModel(input_nodes, output_nodes, middle_layer_size).to(
            self.device
        )
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.0001)
        if output_nodes > 2:
            self.loss = torch.nn.CrossEntropyLoss()
        else:
            self.loss = torch.nn.BCELoss()

    def __str__(self):
        return "Simple MLP Classifier"

    def training(self, training_data, valid_data=None):
        train_data = DataLoader(
            training_data,
            batch_size=32,
            shuffle=True,
            drop_last=True,
        )
        self.model.train()
        for e in range(100):
            losses = []
            for X, y in train_data:
                X, y = (
                    X.to(self.device).float(),
                    y.to(self.device).float(),
                )
                y_pred = self.model(X)
                loss = self.loss(y_pred, y)
                losses.append(loss.cpu().detach())
                loss.backward()
                self.optimizer.step()

            if valid_data:
                result = evaluate_identification(self, valid_data)

    def identification(self, X_id):
        self.model.eval()
        X_id = torch.tensor(X_id).to(self.device).float()
        return self.model(X_id).detach().cpu().numpy()

    def verification(self, X_ver):
        self.model.eval()
        X_ver = torch.tensor(X_ver).to(self.device).float()
        return self.model(X_ver).detach().cpu().numpy()

    def authentication(self, X_auth):
        """
        Take the max probability and use it as a probability of successful authentication.
        """
        self.model.eval()
        X_auth = torch.tensor(X_auth).to(self.device).float()
        y_scores = self.model(X_auth).detach().cpu().numpy()
        return [[x, 1 - x] for x in np.max(y_scores, axis=1)]


if __name__ == "__main__":
    # Load all required data
    NN_SIZE = 128
    INPUT_SIZE = 28
    USER_NUM = 15
    config = {"user_num": USER_NUM, "verbose": 2}
    sup = MedbaSupplier(config)
    # sup = HmogSupplier(config)
    # sup = UciharSupplier(config)
    # sup = ResGaitSupplier(config)
    # sup = LibriSpeechSupplier(config)
    sup.load_datasets()
    # What parts to run
    IDAUTH = False
    VER = False
    STA = True

    if IDAUTH:
        # Train and evaluate identification
        id_train, id_valid, id_test, _ = sup.fetch_and_split_identification()
        identifier = SimpleMLP(
            input_nodes=INPUT_SIZE,
            output_nodes=config["user_num"],
            middle_layer_size=NN_SIZE,
        )
        identifier.training(id_train)
        result = evaluate_identification(identifier, id_test, calculate_entropy=True)
        result.metrics()
        result.visualise()

        # Use the identification model to also evaluate authentication
        *_, auth_adver = sup.fetch_and_split_authentication()
        result = evaluate_authentication(identifier, auth_adver)
        result.metrics()
        result.visualise()
        result.save_results()

    if VER:
        # Train, evaluate, and compare verification
        results = []
        for i in range(config["user_num"]):
            ver_train, _, ver_test, ver_adver = sup.fetch_and_split_verification(i)
            verifier = SimpleMLP(
                input_nodes=INPUT_SIZE, output_nodes=2, middle_layer_size=NN_SIZE
            )
            verifier.training(ver_train)
            result = evaluate_verification(verifier, ver_adver)
            results.append(result)
        compare_results(results)

    # Set the results' file names to the ones saved locally to run this.
    # a = ContinuousResults("Approach 1")
    # a.retrieve_results("2025-03-06T09-23-35_authenticator.json")
    # b = ContinuousResults("Approach 2")
    # b.retrieve_results("2025-03-06T09-26-23_authenticator.json")
    # compare_results((a, b))

    if STA:
        # Evaluate a session takeover attack
        attack_train, _, attack_test, _ = sup.fetch_and_split_session_takeover_attack(
            "verification"
        )
        attack_detector_ver = SimpleMLP(
            input_nodes=INPUT_SIZE,
            output_nodes=2,
            middle_layer_size=NN_SIZE,
        )
        attack_detector_ver.training(attack_train)
        results = evaluate_session_takeover_attack(
            attack_detector_ver.verification, attack_test
        )
        results.metrics()
        results.visualise()

        attack_train, _, attack_test, _ = sup.fetch_and_split_session_takeover_attack(
            "authentication"
        )
        attack_detector_auth = SimpleMLP(
            input_nodes=INPUT_SIZE,
            output_nodes=config["user_num"],
            middle_layer_size=NN_SIZE,
        )
        attack_detector_auth.training(attack_train)
        results = evaluate_authentication(
            attack_detector_auth.authentication, attack_test
        )
        results.metrics()
        results.visualise()
        evaluate_session_takeover_attack(
            attack_detector_auth, attack_test, results.results["eer_threshold"]
        )
