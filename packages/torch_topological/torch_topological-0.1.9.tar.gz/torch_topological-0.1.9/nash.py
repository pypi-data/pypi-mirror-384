import torch
import numpy as np

import matplotlib.pyplot as plt

from sklearn.datasets import make_blobs


def sample_from_sphere(n=100, d=2, r=1, noise=None, ambient=None, seed=None):
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n, d + 1))

    # Normalize points to the sphere
    data = r * data / np.sqrt(np.sum(data**2, 1)[:, None])

    if noise:
        data += noise * rng.standard_normal(data.shape)

    if ambient is not None:
        assert ambient > d
        data = embed(data, ambient)

    return torch.as_tensor(data)


# X = torch.as_tensor(make_blobs(500, 10)[0], dtype=torch.float)

X = sample_from_sphere(n=1000, d=2)
X = torch.hstack((X, torch.zeros((1000, 23))))
X = torch.tensor(X, dtype=torch.float)

input_dim = X.shape[-1]

distance_matrix = torch.cdist(X, X)

directions = [
    torch.as_tensor(sample_from_sphere(n=1, d=d, r=1)[0], dtype=torch.float)
    for d in range(input_dim)
]

directions_tensor = torch.hstack(directions)
directions_tensor = torch.nn.Parameter(directions_tensor)

proj_dim = 23

def project_point(point, normal):
    dist = torch.dot(point, normal)
    projected_point = torch.sub(point, torch.mul(dist, normal))
    return projected_point


def project_on_hyperplane(X, input_dim, direction):
    projected_tensor = torch.empty(0, X.shape[-1])
    for point in X:
        projected_tensor = torch.vstack(
            (projected_tensor, project_point(point, direction))
        )

    _, S, Vh = torch.linalg.svd(projected_tensor, full_matrices=True)
    print(torch.max(1.0 / S))
    V = Vh.mH
    principal_components = V[:, : input_dim - 1]
    res = torch.mm(X, principal_components)
    return res


def forward(X):
    l = X.shape[-1]
    for k in np.arange(0, l):
        s = sum(range(k))
        X = project_on_hyperplane(
            X, X.shape[-1], directions_tensor[k * l - s : k * l - s + (l - k)]
        )
        if proj_dim >= X.shape[-1]:
            break

    return X


learning_rate = 1e-3
n_iters = 20


def loss(mat1, mat2):
    pdist = torch.nn.PairwiseDistance(p=2)
    return pdist(mat1, mat2).mean()


torch.autograd.set_detect_anomaly(True)
optimizer = torch.optim.SGD([directions_tensor], lr=learning_rate)

plt.scatter(X[:, 0], X[:, 1])

for epoch in range(n_iters):
    optimizer.zero_grad()

    y_pred = forward(X)

    l = loss(distance_matrix, torch.cdist(y_pred, y_pred))
    l.backward()

    optimizer.step()

    print("GRAD", directions_tensor.grad)
    print(f"epoch{epoch+1}: loss = {l:.8f}")


y_pred = y_pred.detach().numpy()
plt.scatter(y_pred[:, 0], y_pred[:, 1])
plt.show()
