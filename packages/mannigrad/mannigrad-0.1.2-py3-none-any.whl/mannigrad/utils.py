def mse_loss(preds, targets):
    errors = [(yout - ygt)**2 for ygt, yout in zip(targets, preds)]
    return sum(errors) * (1.0 / len(errors))