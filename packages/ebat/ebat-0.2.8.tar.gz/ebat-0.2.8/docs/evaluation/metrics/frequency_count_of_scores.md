# Frequency Count of Scores

## Overview

The frequency_count_of_scores function calculates the frequency count of scores for legitimate and illegitimate users.

## Parameters

    y_true: A list of ground truth labels, where 0 represents the positive class (legitimate user) and 1 represents the negative class (illegitimate user).
    scores: A list of confidence levels for the positive class of y_true.

## Returns

A dictionary containing two lists:

    legit_scores: A list of scores for legitimate users.
    illegit_scores: A list of scores for illegitimate users.

## Description

The function separates the scores into two lists based on the corresponding ground truth labels. It then returns a
dictionary containing these two lists. This is then visualised when evaluating verification and authentication.
