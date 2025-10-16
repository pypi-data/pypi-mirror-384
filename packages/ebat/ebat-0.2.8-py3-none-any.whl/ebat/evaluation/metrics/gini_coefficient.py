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

import numpy as np


def gini_coefficient(y_true, y_pred):
    """
    Metric suggested by https://dl.acm.org/doi/abs/10.1145/3052973.3053032?casa_token=JibHUJ-q9JwAAAAA:b-X9sXFJxuiRkEKr1W0g91sRh4akXrIRdTSgjcP-zsD3tc_upwyZqFiJcwCyGxYHVmZb4syAY5M
    Calculate per-user success rates and calculate the Gini coefficient.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    users = np.unique(y_true)

    success_rates = []
    for user in users:
        user_preds = y_pred[np.where(y_true == user)]
        success_rate = np.sum(user_preds == user) / len(user_preds)
        success_rates.append(success_rate)
    top_sum = 0
    for xi in success_rates:
        for xj in success_rates:
            top_sum += abs(xi - xj)
    bottom_sum = 2 * len(success_rates) * sum(success_rates)
    return top_sum / bottom_sum
