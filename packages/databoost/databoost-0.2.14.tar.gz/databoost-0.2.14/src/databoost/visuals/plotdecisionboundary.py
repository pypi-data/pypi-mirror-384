def plot_decision_boundary(model, x, y):
    """
    Visualize the decision boundary of a trained PyTorch model on 2D data.

    This function generates a meshgrid across the input space, predicts
    class labels for each grid point using the given model, and plots the
    resulting decision regions along with the original data points. It
    supports both binary and multiclass classification automatically.

    Args:
        model (torch.nn.Module): Trained PyTorch model returning logits.
        x (torch.Tensor): Input features (2D).
        y (torch.Tensor): True labels (binary or multiclass).

    Example:
        >>> from sklearn.datasets import make_moons
        >>> import torch
        >>> x, y = make_moons(n_samples=200, noise=0.2, random_state=42)
        >>> x = torch.tensor(x, dtype=torch.float32)
        >>> y = torch.tensor(y, dtype=torch.float32)
        >>> model = MyModel()
        >>> plot_decision_boundary(model, x, y)
    """
    import torch
    from torch import nn
    import numpy as np
    import matplotlib.pyplot as plt
    
    model.to("cpu")
    x, y = x.to("cpu"), y.to("cpu")


    x_min, x_max = x[:, 0].min() - 0.1, x[:, 0].max() + 0.1
    y_min, y_max = x[:, 1].min() - 0.1, x[:, 1].max() + 0.1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 101), np.linspace(y_min, y_max, 101))

    x_to_pred_on = torch.from_numpy(np.column_stack((xx.ravel(), yy.ravel()))).float()

    model.eval()
    with torch.inference_mode():
        y_logits = model(x_to_pred_on)

    if len(torch.unique(y)) >= 3:
        y_pred = torch.softmax(y_logits, dim=1).argmax(dim=1)
    else:
        y_pred = torch.round(torch.sigmoid(y_logits))

    y_pred = y_pred.reshape(xx.shape).detach().numpy()
    plt.contourf(xx, yy, y_pred, cmap=plt.cm.RdYlBu, alpha=0.7)
    plt.scatter(x[:, 0], x[:, 1], c=y, s=40, cmap=plt.cm.RdYlBu)
    plt.xlim(xx.min(), xx.max())
    plt.ylim(yy.min(), yy.max())
