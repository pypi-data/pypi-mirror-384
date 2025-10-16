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
from sklearn.metrics import pairwise_distances


def average_biometric_information(test_data):
    """Calculate the average biometric information for the test data."""
    print("Calculating distances...")
    intra_dists, inter_dists = calculate_intra_inter_distances(test_data.X, test_data.y)

    entropies = []
    for intra, inter in zip(intra_dists, inter_dists):
        # To avoid zero division
        intra += 10e-10
        inter += 10e-10
        entropies.append(np.sum(intra * np.log2(intra / inter)))
    return np.mean(entropies)


def calculate_intra_inter_distances(X, y, bins=16):
    """Calculate intra and inter distances between data points."""
    num_samples, num_users = y.shape
    all_intra_users = []
    all_inter_users = []
    bins = int(np.sqrt(num_samples / num_users))

    for user in range(num_users):
        user_indices = np.where(y[:, user] == 1)[0]
        user_points = X[user_indices]

        # Calculate intra distances
        intra_dists = pairwise_distances(user_points, user_points, metric="euclidean")
        intra_dists = intra_dists[np.triu_indices(len(user_indices), k=1)]
        intra_dist, _ = np.histogram(intra_dists, bins=bins)
        intra_dist = intra_dist / np.sum(intra_dist)
        all_intra_users.append(intra_dist)

        # Calculate inter distances
        inter_dists = []
        for other_user in range(num_users):
            if other_user != user:
                other_user_indices = np.where(y[:, other_user] == 1)[0]
                other_user_points = X[other_user_indices]
                inter_dists.extend(
                    pairwise_distances(
                        user_points, other_user_points, metric="euclidean"
                    ).flatten()
                )
        inter_dist, _ = np.histogram(inter_dists, bins=bins)
        inter_dist = inter_dist / np.sum(inter_dist)
        all_inter_users.append(inter_dist)

    return all_intra_users, all_inter_users
