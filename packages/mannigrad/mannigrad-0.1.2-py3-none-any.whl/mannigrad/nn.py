import random
from engine import Value 

class Neuron:
    def __init__(self,nin,activation=None):
        self.weights = [Value(random.uniform(-1, 1)) for _ in range(nin)]
        self.bias = Value(random.uniform(-1, 1))
        self.activation = activation

    def __call__(self,x):
        act = sum(wi*xi for wi,xi in zip(self.weights,x)) + self.bias
        if self.activation is None:
            out = act # linear acti
        else:
            out = self.activation(act)
        return out
    
    def parameters(self):
        return self.weights + [self.bias]
    
    def __repr__(self):
        return f"Neuron(nin={len(self.weights)}, activation={self.activation})"

class Layer:
    def __init__(self,nin,nout,activation=None):
        self.neurons = [Neuron(nin,activation) for _ in range(nout)]

    def __call__(self,x):
        out = [n(x) for n in self.neurons]
        return out
    
    def parameters(self):
        params = []
        for neuron in self.neurons:
            params.extend(neuron.parameters())
        return params
    
    def __repr__(self):
        return f"Layer({len(self.neurons)} neurons)"

class MLP:
    def __init__(self, nin, nouts, activations=None):
        sz = [nin] + nouts
        self.layers = []
        for i in range(len(nouts)):
            act = None if activations is None else activations[i]
            self.layers.append(Layer(sz[i], sz[i+1], activation=act))
    def __call__(self,x):
        for layer in self.layers:
            x = layer(x)
        return x[0] if len(x) == 1 else x
    
    def __repr__(self):
        return f"MLP({', '.join(str(layer) for layer in self.layers)})"
    
    def parameters(self):
        params = []
        for layer in self.layers:
            params.extend(layer.parameters())
        return params

class Optimizer:
    def __init__(self, params, lr=0.01):
        self.params = list(params)  
        self.lr = lr

    def step(self):
        raise NotImplementedError  # to be implemented in subclasses

    def zero_grad(self):
        for p in self.params:
            if hasattr(p, 'grad'):
                p.grad = 0.0

class SGD(Optimizer):
    def __init__(self, params, lr=0.01):
        super().__init__(params, lr)

    def step(self):
        for p in self.params:
            if hasattr(p, 'grad'):
                p.data -= self.lr * p.grad


class Adam(Optimizer):
    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        super().__init__(params, lr)
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = [0.0 for _ in self.params]
        self.v = [0.0 for _ in self.params]
        self.t = 0

    def step(self):
        self.t += 1
        for i, p in enumerate(self.params):
            if hasattr(p, 'grad'):
                self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad
                self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (p.grad ** 2)

                m_hat = self.m[i] / (1 - self.beta1 ** self.t)
                v_hat = self.v[i] / (1 - self.beta2 ** self.t)
                
                p.data -= self.lr * m_hat / ((v_hat ** 0.5) + self.eps)

