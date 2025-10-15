# warpgbm/metrics.py

import torch

def rmsle_torch(y_true, y_pred, eps=1e-7):
    y_true = torch.clamp(y_true, min=0)
    y_pred = torch.clamp(y_pred, min=0)
    log_true = torch.log1p(y_true + eps)
    log_pred = torch.log1p(y_pred + eps)
    return torch.sqrt(torch.mean((log_true - log_pred) ** 2))

def softmax(logits, dim=-1):
    """Numerically stable softmax"""
    exp_logits = torch.exp(logits - torch.max(logits, dim=dim, keepdim=True)[0])
    return exp_logits / torch.sum(exp_logits, dim=dim, keepdim=True)

def log_loss_torch(y_true_labels, y_pred_probs, eps=1e-15):
    """
    Compute log loss (cross-entropy) for multiclass classification
    
    Args:
        y_true_labels: 1D tensor of true class labels (integers)
        y_pred_probs: 2D tensor of predicted probabilities [n_samples, n_classes]
        eps: Small value to clip probabilities for numerical stability
    """
    y_pred_probs = torch.clamp(y_pred_probs, eps, 1 - eps)
    n_samples = y_true_labels.shape[0]
    
    # Get the predicted probability for the true class
    true_class_probs = y_pred_probs[torch.arange(n_samples), y_true_labels.long()]
    
    # Return negative log likelihood
    return -torch.mean(torch.log(true_class_probs))

def accuracy_torch(y_true_labels, y_pred_labels):
    """Compute accuracy"""
    return (y_true_labels == y_pred_labels).float().mean()
