[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-lightgrey.svg)](https://spdx.org/licenses/Apache-2.0.html)

This project is licensed under the **Apache License 2.0**.  
See `LICENSE` and `NOTICE` for details. © 2025 Noor Jamaludeen

# Online-Behavioral-Modeling
This Python package enables the online discovery of behavioral patterns in trial-by-trial experiments. In trial-by-trial experiments, a participant (human/animal) is exposed to a series of stimuli and is expected to respond. The behavioral pattern is defined as the quantification of the contributions of stimulus features to the prediction of the response, taking into account the effects from prior trials.  

# Format of input data
The behavioral data should be formatted as a pandas dataframe where the trials are chronologically ordered. Each trial/row consists of a stimulus described by a set of features and a corresponding response. 

# An Example of usage:
Input arguments:
par: Name/ID of participant,
effect_var: response
parent_cause_vars: stimulus features
lags: list of numbers of prior trials
simulator_types: list of simulator types to be employed [0='NP',1='OP',2='UP']
output_file: path of file to output the results of hyperparameter tuning
default_missing_value: value to be used to refer to missing <stimulus feature value, response value> pairs.
dt_runs: number of runs for the decision tree model to account for non-determinism,
eval_method: evaluation method used to evaluate the performance of the simulator [Leave_one_out,KFold,StratifiedKFold,RepeatedStratifiedKFold],
eval_method_model_selection: evaluation method used to select the best machine learning algorithm [Leave_one_out,KFold,StratifiedKFold,RepeatedStratifiedKFold],
svm_model: Support vector machine classifier for categorical response and Support Vector machine Regressor for numeric response,
dt_model: Decision Tree classifier for categorical response and Decision Tree Regressor for numeric response
num_processes: Number of processes 
k: number of folds for evaluation
r: number of repetitions for evaluation


behavioral_pattern_object = behaviour_constructor.behaviourConstructor(par, effect_var, parent_cause_vars, [lag],
                                                                   simulator_types=[simulator],
                                                                   output_file=directory,
                                                                   default_missing_value=0, dt_runs=runs,
                                                                   eval_method=LeaveOneOut(), category=None,
                                                                   eval_method_model_selection=RepeatedStratifiedKFold(
                                                                       n_splits=k, n_repeats=r),
                                                                   svm_model=svm.SVC,
                                                                   dt_model=tree.DecisionTreeClassifier
                                                                   , num_processes=processors, k=k, r=r,max_lag_var=max_lag)

behavioral_pattern,_,_,_=behavioral_pattern_object.generate_behavioural_pattern(data_window[parent_cause_vars+[effect_var]])
The object behavioral_pattern contains the quantification of the stimulus features to the response. Each value ranges from 0 to 1 with higher values indicating stronger contributions.

                                                                               




