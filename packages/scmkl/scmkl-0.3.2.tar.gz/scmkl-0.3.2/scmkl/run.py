import anndata as ad
import numpy as np
import time
import tracemalloc

from scmkl.train_model import train_model
from scmkl.test import predict, find_selected_groups


def run(adata: ad.AnnData, alpha_list: np.ndarray, 
        metrics: list | None = None, 
        return_probs: bool=False) -> dict:
    """
    Wrapper function for training and test with multiple alpha values.
    Returns metrics, predictions, group weights, and resource usage.

    Parameters
    ----------
    adata : ad.AnnData 
        A processed `ad.AnnData` with `'Z_train'`, `'Z_test'`, and 
        `'group_dict'` keys in `adata.uns`.
    
    alpha_list : np.ndarray 
        Sparsity values to create models with. Alpha refers to the 
        penalty parameter in Group Lasso. Larger alphas force group 
        weights to shrink towards zero while smaller alphas apply a 
        lesser penalty to kernal weights. Values too large will results 
        in models that weight all groups as zero.

    metrics : list[str]
        Metrics that should be calculated on predictions. Options are 
        `['AUROC', 'F1-Score', 'Accuracy', 'Precision', 'Recall']`. 
        When set to `None`, all metrics are calculated.
    
    Returns
    -------
    results : dict
        Results with keys and values: 

        `'Metrics'` (dict): 
        A nested dictionary as `[alpha][metric] = value`.

        `'Group_names'` (np.ndarray): 
        Array of group names used in model(s).
    
        `'Selected_groups'` (dict): 
        A nested dictionary as `[alpha] = np.array([nonzero_groups])`.
        Nonzero groups are groups that had a kernel weight above zero.

        `'Norms'` (dict): 
        A nested dictionary as `[alpha] = np.array([kernel_weights])`
        Order of `kernel_weights` is respective to `'Group_names'` 
        values.

        `'Observed'` (np.nparray): 
        An array of ground truth cell labels from the test set.

        `'Predictions'` (dict): 
        A nested dictionary as `[alpha] = predicted_class` respective 
        to `'Observations'` for `alpha`.

        `'Test_indices'` (np.array: 
        Indices of samples respective to adata used in the training 
        set.

        `'Model'` (dict): 
        A nested dictionary where `[alpha] = celer.GroupLasso` object 
        for `alpha`.

        `'RAM_usage'` (dict): 
        A nested dictionary with memory usage in GB after 
        training models for each `alpha`.

    Examples
    --------
    >>> results = scmkl.run(adata = adata, 
    ...                     alpha_list = np.array([0.05, 0.1, 0.5]))
    >>> results
    dict_keys(['Metrics', 'Selected_groups', 'Norms', 'Predictions', 
    ...        'Observed', 'Test_indices', 'Group_names', 'Models', 
    ...        'Train_time', 'RAM_usage'])
    >>>
    >>> alpha values
    >>> results['Metrics'].keys()
    dict_keys([0.05, 0.1, 0.5])
    >>>
    >>> results['Metrics'][0.05]
    {'AUROC': 0.9859,
    'Accuracy': 0.945,
    'F1-Score': 0.9452736318407959,
    'Precision': 0.9405940594059405,
    'Recall': 0.95}
    """
    if metrics is None:
        metrics = ['AUROC', 'F1-Score','Accuracy', 'Precision', 'Recall']

    # Initializing variables to capture metrics
    group_names = list(adata.uns['group_dict'].keys())
    preds = {}
    group_norms = {}
    mets_dict = {}
    selected_groups = {}
    train_time = {}
    models = {}
    probs = {}

    D = adata.uns['D']

    # Generating models for each alpha and outputs
    tracemalloc.start()
    for alpha in alpha_list:
        
        print(f'  Evaluating model. Alpha: {alpha}', flush = True)

        train_start = time.time()

        adata = train_model(adata, group_size= 2*D, alpha = alpha)

        if return_probs:
            alpha_res = predict(adata, 
                                metrics = metrics,
                                return_probs = return_probs)
            preds[alpha], mets_dict[alpha], probs[alpha] = alpha_res

        else:
            alpha_res = predict(adata, 
                                metrics = metrics,
                                return_probs = return_probs)
            preds[alpha], mets_dict[alpha] = alpha_res

        selected_groups[alpha] = find_selected_groups(adata)

        kernel_weights = adata.uns['model'].coef_
        group_norms[alpha] = [
            np.linalg.norm(kernel_weights[i * 2 * D : (i + 1) * 2 * D - 1])
            for i in np.arange(len(group_names))
            ]
        
        models[alpha] = adata.uns['model']
        
        train_end = time.time()
        train_time[alpha] = train_end - train_start

    # Combining results into one object
    results = {}
    results['Metrics'] = mets_dict
    results['Selected_groups'] = selected_groups
    results['Norms'] = group_norms
    results['Predictions'] = preds
    results['Observed'] = adata.obs['labels'].iloc[adata.uns['test_indices']]
    results['Test_indices'] = adata.uns['test_indices']
    results['Group_names']= group_names
    results['Models'] = models
    results['Train_time'] = train_time
    results['RAM_usage'] = f'{tracemalloc.get_traced_memory()[1]/1e9} GB'
    results['Probabilities'] = probs

    return results