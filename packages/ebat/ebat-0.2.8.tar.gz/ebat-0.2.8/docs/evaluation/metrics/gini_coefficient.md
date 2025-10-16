# Gini Coefficient

## Overview

The gini_coefficient function calculates the Gini coefficient of the authentication success rates of legitimate users.

## Parameters

    y_true: A list of zero-indexed legitimate user class ground truths.
    y_pred: A list of zero-indexed legitimate user class predictions.

## Returns

A single float value of the Gini coefficient.

## Description

The function calculates the Gini coefficient by first calculating the per-user authentication success rates and then
averaging the absolute difference of all success rate pairs. 