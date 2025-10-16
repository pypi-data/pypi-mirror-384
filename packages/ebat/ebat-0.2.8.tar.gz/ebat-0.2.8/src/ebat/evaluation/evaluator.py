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

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    precision_recall_fscore_support,
    accuracy_score,
    det_curve,
    matthews_corrcoef,
    roc_curve,
    confusion_matrix,
)

from plotly import graph_objects as go

from ebat.evaluation.metrics.frequency_count_of_scores import (
    frequency_count_of_scores,
)
from ebat.evaluation.metrics.gini_coefficient import gini_coefficient
from ebat.evaluation.metrics.biometric_information import (
    average_biometric_information,
)


class ResultsBase:

    def __init__(self, approach_name, calculate_entropy, decimal_places=3):
        self.results = {}
        self.approach_name = approach_name
        self.decimal_places = decimal_places
        self.save_path = Path(os.getcwd()) / "results"
        self.calculate_entropy = calculate_entropy

    def add_metric(self, name, value):
        self.results[name] = value

    def save_results(self):
        self.save_path.mkdir(exist_ok=True)
        file_name = (
            f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}_{self.approach_name}.json"
        )
        with open(self.save_path / file_name, "w") as save_file:
            json.dump(self.results, save_file)

    def retrieve_results(self, results_name):
        with open(self.save_path / results_name, "r") as save_file:
            self.results = json.load(save_file)


class OneoffResults(ResultsBase):

    def __init__(self, approach_name, calculate_entropy):
        super().__init__(approach_name, calculate_entropy)

    def metrics(self):
        print(f"Accuracy: {round(self.results['acc'], self.decimal_places)}")
        print(f"Precision: {round(self.results['prec'], self.decimal_places)}")
        print(f"Recall: {round(self.results['rec'], self.decimal_places)}")
        print(f"F1 Score: {round(self.results['f1'], self.decimal_places)}")
        print(
            f"Matthews Corr. Coef.: {round(self.results['mcc'], self.decimal_places)}"
        )
        print(f"Gini Coef.: {round(self.results['gini'], self.decimal_places)}")
        if self.calculate_entropy:
            print(
                f"Biometric Information: {round(self.results['abi'], self.decimal_places)}"
            )

    def visualise(self):
        fig = go.Figure(
            data=go.Heatmap(
                x=[f"User {x + 1}" for x in range(len(self.results["cm"][0]))],
                y=[f"User {x + 1}" for x in range(len(self.results["cm"][0]))],
                z=self.results["cm"],
            )
        )
        fig.update_layout(
            {
                "title": "Per-user Confusion Matrix",
                "xaxis_title": "Predicted User",
                "yaxis_title": "True User",
            }
        )
        fig.show()


class ContinuousResults(ResultsBase):

    def __init__(self, approach_name, calculate_entropy):
        super().__init__(approach_name, calculate_entropy)

    def metrics(self):
        print(f"Equal Error Rate: {round(self.results['eer'], self.decimal_places)}")
        if self.calculate_entropy:
            print(
                f"Biometric Information: {round(self.results['rel_ent'], self.decimal_places)}"
            )

    def visualise(self):
        fig = go.Figure(
            data=go.Scatter(
                x=self.results["roc_curve"]["tpr"], y=self.results["roc_curve"]["fpr"]
            ),
        )
        fig.update_layout(
            {
                "title": "Receiver Operating Characteristic Curve",
                "xaxis_title": "False Positive Rate",
                "xaxis_range": [0, 1],
                "yaxis_title": "True Positive Rate",
                "yaxis_range": [0, 1],
                "font_size": 20,
            }
        )
        fig.show()

        fig = go.Figure(
            data=go.Scatter(
                x=self.results["det_curve"]["far"], y=self.results["det_curve"]["frr"]
            )
        )
        fig.update_layout(
            {
                "title": "Detection Error Tradeoff Curve",
                "xaxis": {
                    "title": "False Positive Rate",
                    "type": "log",
                },
                "yaxis": {
                    "title": "False Negative Rate",
                    "type": "log",
                },
                "font_size": 20,
            }
        )
        fig.show()

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=self.results["det_curve"]["thresholds"],
                    y=self.results["det_curve"]["far"],
                    name="FAR",
                ),
                go.Scatter(
                    x=self.results["det_curve"]["thresholds"],
                    y=self.results["det_curve"]["frr"],
                    name="FRR",
                ),
            ]
        )
        fig.update_layout(
            {
                "title": "FAR vs. FRR Curves",
                "xaxis_title": "Threshold",
                "xaxis_range": [0, 1],
                "yaxis_title": "Rates",
                "yaxis_range": [0, 1],
                "font_size": 20,
            }
        )
        fig.show()

        # Automatically calculate the number of bins
        nbins = (
            (
                len(self.results["fcs"]["legit_scores"])
                + len(self.results["fcs"]["illegit_scores"])
            )
            // 2
            // 10
        )
        fig = go.Figure(
            data=[
                go.Histogram(
                    x=self.results["fcs"]["legit_scores"],
                    name="Legitimate",
                    nbinsx=nbins,
                ),
                go.Histogram(
                    x=self.results["fcs"]["illegit_scores"],
                    name="Illegitimate",
                    nbinsx=nbins,
                ),
            ]
        )
        fig.update_layout(
            {
                "title": "Frequency Count of Scores",
                "xaxis_title": "Score",
                "yaxis_title": "Frequency Count",
                "barmode": "overlay",
                "font_size": 20,
            }
        )
        fig.update_traces({"opacity": 0.75})
        fig.show()


class STAResults(ContinuousResults):
    """
    Results of the session takeover attack.
    """

    def __init__(self, approach_name, calculate_entropy):
        super().__init__(approach_name, calculate_entropy)

    def visualise(self):
        super().visualise()
        print("ASDFAWEFAWEF")
        try:
            fig = go.Figure(
                data=go.Scatter(
                    x=[i for i in range(len(self.results["sta"]["y_scores"]))],
                    y=self.results["sta"]["y_scores"],
                )
            )
            fig.add_hline(self.results["sta"]["threshold"], line_color="green")
            fig.add_vline(self.results["sta"]["attack_point"], line_color="red")
            fig.update_layout(
                {
                    "title": "Session Takeover Attack Score Development",
                    "xaxis_title": "Time (red vline -- point of attack)",
                    "yaxis_title": "Predicted Score (green hline -- threshold)",
                }
            )
            fig.show()
        except Exception as e:
            print(f"Error creating graph in STAResults: {e}")


# Calculation of evaluation metrics


def evaluate_identification(
    identifier, id_data, approach_name="identifier", calculate_entropy=False
):
    X_test = id_data.X
    y_test = list(np.argmax(id_data.y, axis=1))
    y_pred = np.argmax(identifier.identification(X_test), axis=1)

    results = OneoffResults(approach_name, calculate_entropy)
    results.add_metric("cm", confusion_matrix(y_test, y_pred).tolist())
    results.add_metric("acc", accuracy_score(y_test, y_pred))
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="weighted", zero_division=0
    )
    results.add_metric("prec", prec)
    results.add_metric("rec", rec)
    results.add_metric("f1", f1)
    results.add_metric("mcc", matthews_corrcoef(y_test, y_pred))
    results.add_metric("gini", gini_coefficient(y_test, y_pred))
    if calculate_entropy:
        results.add_metric("abi", average_biometric_information(id_data))
    return results


def calculate_continuous(
    X_test, y_true, y_pred, approach_name, calculate_entropy, sta=False
):
    if sta:
        results = STAResults(approach_name, calculate_entropy)
    else:
        results = ContinuousResults(approach_name, calculate_entropy)

    fpr, tpr, thresholds_roc = roc_curve(y_true, y_pred)
    results.add_metric(
        "roc_curve",
        {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": thresholds_roc.tolist(),
        },
    )
    far, frr, thresholds_det = det_curve(y_true, y_pred, pos_label=0)
    results.add_metric(
        "det_curve",
        {
            "far": far.tolist(),
            "frr": frr.tolist(),
            "thresholds": thresholds_det.tolist(),
        },
    )
    results.add_metric("fcs", frequency_count_of_scores(y_true, y_pred))

    deltas = [abs(x - y) for x, y in zip(far, frr)]
    min_i = np.argmin(deltas)
    results.add_metric("eer", (far[min_i] + frr[min_i]) / 2)
    results.add_metric("eer_threshold", thresholds_det[min_i])
    if calculate_entropy:
        results.add_metric("abi", average_biometric_information(X_test))
    return results


def evaluate_verification(
    verifier, auth_data, approach_name="verifier", calculate_entropy=False
):
    # 0, 1 vector of ground truth (0 — auth user, 1 attackers)
    y_true = np.argmax(auth_data.y, axis=1)
    y_scores = verifier.verification(auth_data.X)
    # Probability of positive class (auth user) as required by curve functions.
    y_scores = [x[0] for x in y_scores]
    return calculate_continuous(
        auth_data.X, y_true, y_scores, approach_name, calculate_entropy
    )


def evaluate_authentication(
    authenticator, auth_data, approach_name="authenticator", calculate_entropy=False
):
    y_true = np.argmax(auth_data.y, axis=1)
    y_scores = authenticator.authentication(auth_data.X)
    y_scores = [x[0] for x in y_scores]
    return calculate_continuous(
        auth_data.X, y_true, y_scores, approach_name, calculate_entropy
    )


def evaluate_session_takeover_attack(
    attack_detection_method,
    attack_data,
    threshold=None,
    approach_name="attack_detector",
    calculate_entropy=False,
):
    y_true = np.argmax(attack_data.y, axis=1)
    y_scores = attack_detection_method(attack_data.X)
    y_scores = np.array([float(x[0]) for x in y_scores])
    attack_point = int(np.where(y_true == 1)[0][0])
    results = calculate_continuous(
        attack_data.X, y_true, y_scores, approach_name, calculate_entropy, sta=True
    )
    results.add_metric(
        "sta",
        {
            "y_true": y_true.tolist(),
            "y_scores": y_scores.tolist(),
            "attack_point": attack_point,
            "threshold": threshold if threshold else results.results["eer_threshold"],
        },
    )
    return results


def compare_results(results):
    roc_data, det_data = [], []
    for i, result in enumerate(results):
        roc_data.append(
            go.Scatter(
                x=result.results["roc_curve"]["tpr"],
                y=result.results["roc_curve"]["fpr"],
                name=result.approach_name,
            )
        )
        det_data.append(
            go.Scatter(
                x=result.results["det_curve"]["far"],
                y=result.results["det_curve"]["frr"],
                name=result.approach_name,
            )
        )
    fig = go.Figure(data=roc_data)
    fig.update_layout(
        {
            "title": "Receiver Operating Characteristic Curve",
            "xaxis_title": "False Positive Rate",
            "xaxis_range": [0, 1],
            "yaxis_title": "True Positive Rate",
            "yaxis_range": [0, 1],
            "font_size": 30,
        }
    )
    fig.show()

    fig = go.Figure(data=det_data)
    fig.update_layout(
        {
            "title": "Detection Error Tradeoff Curve",
            "xaxis_title": "False Positive Rate",
            "xaxis_type": "log",
            "yaxis_title": "False Negative Rate",
            "yaxis_type": "log",
            "font_size": 30,
        }
    )
    fig.show()
