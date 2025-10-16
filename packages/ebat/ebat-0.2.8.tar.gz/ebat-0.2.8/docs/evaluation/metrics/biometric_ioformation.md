# Average Biometric Information

## Overview

The average_relative_entropy function calculates the average biometric information (ABI) of the data provided to it.

## Parameters

    test_data: an EBAT dataset for which we would like to calculate the ABI

## Returns

A single float value of ABI.

## Description

The function calculates the ABI by first calculating the Euclidean distances between data samples in the dataset and
split them to intra- and inter-user distances for each of the users. Next, we apply a histogram to both intra- and
inter-user distances with a predetermined number of bins set to the square root of number of samples divided by the
number of users: `sqrt(num_samples/num_users)`. We normalise each histogram by dividing its elements with the sum of its
elements to obtain probability distributions of the distances. Then we calculate the Kullback-Leibler divergence between
intra- and inter-distances for each user and return the mean of the calculated values.    