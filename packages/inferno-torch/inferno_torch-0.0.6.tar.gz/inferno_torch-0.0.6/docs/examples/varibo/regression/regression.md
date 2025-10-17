# Regression on Toy Data

This toy example shows how to train a variational neural network via *implicit* regularization via SGD initialized to the prior as described in [this paper](https://arxiv.org/abs/2505.20235). This avoids the computational cost of regularization which for non-trivial variational families is often significant and preserves beneficial inductive biases.

You can run this example yourself via the corresponding [standalone script](run.py).

## Data

We begin by generating some synthetic training and test data.

<figure markdown="1">
![Data](plots/data.svg)
</figure>

## Model

Next, we define a fully-connected stochastic neural network using a pre-defined [``models.MLP``](../../../api/models.md#inferno.models.MLP).

```python title="Model"
--8<-- "docs/examples/varibo/regression/run.py:model"
```

1.  PyTorch ``nn.Module``s can be used as part of ``inferno`` models.


## Training

We train the model via the expected loss, 
\(
\bar{\ell}(\theta) = \mathbb{E}_{q_\theta(w)}[\ell(y, f_w(X))]
\)
i.e. the average loss of the model when drawing weights from the variational distribution \(q_\theta(w)\).
In practice, for efficiency we only use a single sample per batch during training.

```python title="Training"
--8<-- "docs/examples/varibo/regression/run.py:training"
```

## Results

### Learning Curves

<figure markdown="1">
![Learning Curves](plots/learning_curves.svg)
</figure>

### Prediction

<figure markdown="1">
![Predictions](plots/predictions.svg)
</figure>

<!-- 
Show code above but don't execute and include generated plots.

- How to format code blocks: https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#usage
- Options for including code from a separate file: https://facelessuser.github.io/pymdown-extensions/extensions/snippets/#snippets-notation
- Options for executing code in blocks: https://pawamoy.github.io/markdown-exec/usage/#render-the-source-code-as-well
- Options for displaying plots: https://pawamoy.github.io/markdown-exec/gallery/#with-matplotlib
- Options for sharing variables between code blocks etc.: https://pawamoy.github.io/markdown-exec/usage
-->


