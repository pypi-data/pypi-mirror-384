# machinery
import unittest as ut
import numpy as np

import pureml as pm
import pureml.machinery as mach


def _rng(seed=0):
    return np.random.default_rng(seed)


class TestTensorBasics(ut.TestCase):
    def test_init_and_shape(self):
        x = pm.Tensor(np.arange(6, dtype=np.float64).reshape(2, 3), requires_grad=True)
        self.assertTrue(x.requires_grad)
        self.assertIsNone(x.grad)
        self.assertEqual(x.shape, (2, 3))
        np.testing.assert_array_equal(x.data, np.array([[0, 1, 2], [3, 4, 5]], dtype=np.float64))

    def test_requires_grad_propagation_and_no_grad(self):
        a = pm.Tensor(np.ones((2, 2)), requires_grad=True)
        b = pm.Tensor(np.ones((2, 2)), requires_grad=False)
        y = a + b
        self.assertTrue(y.requires_grad)

        with pm.no_grad():
            z = a + b
            self.assertFalse(pm.is_grad_enabled())
            self.assertFalse(z.requires_grad)
        # back to normal
        self.assertTrue(pm.is_grad_enabled())


class TestElementwiseAutograd(ut.TestCase):
    def test_square_backward(self):
        rng = _rng(1)
        x = pm.Tensor(rng.standard_normal((4, 5)), requires_grad=True)
        y = x * x                # y has same shape; backward seeds ones_like
        y.backward()
        np.testing.assert_allclose(x.grad, 2.0 * x.data, rtol=1e-6, atol=1e-8)

    def test_custom_upstream_grad(self):
        rng = _rng(2)
        x = pm.Tensor(np.abs(rng.standard_normal((3, 4))) + 0.5, requires_grad=True)
        y = x ** pm.Tensor(np.ones_like(x.data))  # effectively identity but keeps autograd path
        upstream = np.full_like(y.data, 0.5)
        y.backward(upstream)
        # dy/dx = 1 → dL/dx = upstream
        np.testing.assert_allclose(x.grad, upstream, rtol=1e-6, atol=1e-8)

    def test_truediv_grad(self):
        rng = _rng(3)
        a = pm.Tensor(rng.uniform(0.5, 1.5, (3, 3)), requires_grad=True)
        b = pm.Tensor(rng.uniform(0.5, 1.5, (3, 3)), requires_grad=True)
        z = a / b
        z.backward()  # upstream = 1
        # dz/da = 1/b ; dz/db = -a/b^2
        np.testing.assert_allclose(a.grad, 1.0 / b.data, rtol=1e-6, atol=1e-8)
        np.testing.assert_allclose(b.grad, -(a.data / (b.data ** 2)), rtol=1e-6, atol=1e-8)

    def test_fanout_grad_accumulates(self):
        x = pm.Tensor(np.array([1.0, 2.0, 3.0]), requires_grad=True)
        y1 = x * pm.Tensor(np.array([2.0, 2.0, 2.0]))  # dy1/dx = 2
        y2 = x * pm.Tensor(np.array([3.0, 3.0, 3.0]))  # dy2/dx = 3
        z  = y1 + y2                                   # dz/dx = 5
        z.backward()                                   # upstream 1
        np.testing.assert_allclose(x.grad, np.array([5.0, 5.0, 5.0]), rtol=1e-6, atol=1e-8)


class TestBroadcasting(ut.TestCase):
    def test_add_broadcast_grad(self):
        x = pm.Tensor(np.ones((2, 3)), requires_grad=True)
        y = pm.Tensor(np.array([[10.0, 20.0, 30.0]]), requires_grad=True)  # (1,3)
        z = x + y                      # (2,3)
        z.backward()                   # upstream ones
        # dx = 1
        np.testing.assert_allclose(x.grad, np.ones_like(x.data), rtol=1e-6, atol=1e-8)
        # dy = sum over axis=0 (because y broadcast on axis 0): 2 rows → 2
        np.testing.assert_allclose(y.grad, np.array([[2.0, 2.0, 2.0]]), rtol=1e-6, atol=1e-8)

    def test_mul_broadcast_grad(self):
        x = pm.Tensor(np.array([[1.0], [2.0], [3.0]]), requires_grad=True)  # (3,1)
        y = pm.Tensor(np.array([[4.0, 5.0, 6.0, 7.0]]), requires_grad=True) # (1,4)
        z = x * y                         # (3,4)
        z.backward()                      # upstream ones
        # dx = sum over broadcasted axis=1: sum(y) = 4+5+6+7 = 22, repeated for 3 rows
        np.testing.assert_allclose(x.grad, np.array([[22.0], [22.0], [22.0]]), rtol=1e-6, atol=1e-8)
        # dy = sum over broadcasted axis=0: sum(x) = 1+2+3 = 6, repeated across 4 cols
        np.testing.assert_allclose(y.grad, np.array([[6.0, 6.0, 6.0, 6.0]]), rtol=1e-6, atol=1e-8)


class TestMatrixOps(ut.TestCase):
    def test_matmul_grad(self):
        rng = _rng(4)
        A = pm.Tensor(rng.standard_normal((2, 3)), requires_grad=True)
        B = pm.Tensor(rng.standard_normal((3, 4)), requires_grad=True)
        Y = A @ B                              # (2,4)
        Y.backward()                           # upstream ones
        up = np.ones_like(Y.data)
        dA_expected = up @ B.data.T            # (2,3)
        dB_expected = A.data.T @ up            # (3,4)
        np.testing.assert_allclose(A.grad, dA_expected, rtol=1e-6, atol=1e-8)
        np.testing.assert_allclose(B.grad, dB_expected, rtol=1e-6, atol=1e-8)

    def test_batched_matmul_grad(self):
        rng = _rng(5)
        A = pm.Tensor(rng.standard_normal((5, 2, 3)), requires_grad=True)
        B = pm.Tensor(rng.standard_normal((5, 3, 4)), requires_grad=True)
        Y = A @ B                              # (5,2,4)
        Y.backward()
        up = np.ones_like(Y.data)
        dA_expected = up @ np.swapaxes(B.data, -1, -2)       # (5,2,3)
        dB_expected = np.swapaxes(A.data, -1, -2) @ up       # (5,3,4)
        np.testing.assert_allclose(A.grad, dA_expected, rtol=1e-6, atol=1e-8)
        np.testing.assert_allclose(B.grad, dB_expected, rtol=1e-6, atol=1e-8)

    def test_transpose_grad(self):
        X = pm.Tensor(np.arange(6.0).reshape(2, 3), requires_grad=True)
        Y = X.T                                # (3,2)
        Y.backward()                           # upstream ones
        # dX = transpose(ones_like(Y))
        np.testing.assert_allclose(X.grad, np.ones_like(X.data), rtol=1e-6, atol=1e-8)


class TestReshapeFlatten(ut.TestCase):
    def test_reshape_backward(self):
        rng = _rng(6)
        X = pm.Tensor(rng.standard_normal((2, 3, 4)), requires_grad=True)
        Y = X.reshape(6, 4)
        Y.backward()                           # upstream ones → just reshaped back
        np.testing.assert_allclose(X.grad, np.ones_like(X.data), rtol=1e-6, atol=1e-8)

    def test_flatten_keep_batch(self):
        X = pm.Tensor(np.arange(2*3*4.0).reshape(2, 3, 4), requires_grad=True)
        Y = X.flatten(keep_batch=True)         # (2, 12)
        self.assertEqual(Y.data.shape, (2, 12))
        Y.backward()                           # upstream ones
        np.testing.assert_allclose(X.grad, np.ones_like(X.data), rtol=1e-6, atol=1e-8)

    def test_flatten_all(self):
        X = pm.Tensor(np.arange(24.0).reshape(2, 3, 4), requires_grad=True)
        Y = X.flatten(keep_batch=False)        # (24,)
        self.assertEqual(Y.data.shape, (24,))
        Y.backward()
        np.testing.assert_allclose(X.grad, np.ones_like(X.data), rtol=1e-6, atol=1e-8)


class TestElementaryFns(ut.TestCase):
    def test_ln_grad(self):
        x = pm.Tensor(np.array([0.5, 1.0, 2.0]), requires_grad=True)
        y = mach.ln(x)
        y.backward()                           # upstream ones
        np.testing.assert_allclose(x.grad, 1.0 / x.data, rtol=1e-6, atol=1e-8)

    def test_log2_grad(self):
        x = pm.Tensor(np.array([0.5, 1.0, 2.0]), requires_grad=True)
        y = mach.log2(x)
        y.backward()
        np.testing.assert_allclose(x.grad, 1.0 / (x.data * np.log(2.0)), rtol=1e-6, atol=1e-8)

    def test_sqrt_grad(self):
        x = pm.Tensor(np.array([0.5, 1.0, 2.0]), requires_grad=True)
        y = mach.sqrt(x)
        y.backward()
        np.testing.assert_allclose(x.grad, 0.5 / np.sqrt(x.data), rtol=1e-6, atol=1e-8)


class TestNonDiffAndGraphUtils(ut.TestCase):
    def test_argmax_is_nondiff(self):
        X = pm.Tensor(np.array([[1.0, 3.0, 2.0]]), requires_grad=True)
        idx = X.argmax(axis=-1)
        self.assertFalse(idx.requires_grad)
        np.testing.assert_array_equal(idx.data, np.array([1]))

    def test_backward_noop_when_requires_grad_false(self):
        X = pm.Tensor(np.array([1.0, 2.0, 3.0]), requires_grad=False)
        # Should not raise
        X.backward()
        self.assertIsNone(X.grad)

    def test_zero_grad_graph(self):
        x = pm.Tensor(np.array([1.0, 2.0, 3.0]), requires_grad=True)
        y = x * x
        y.backward()
        self.assertIsNotNone(x.grad)
        self.assertIsNotNone(y.grad)
        y.zero_grad_graph()
        self.assertIsNone(x.grad)
        self.assertIsNone(y.grad)

    def test_detach_graph(self):
        x = pm.Tensor(np.array([1.0, 2.0, 3.0]), requires_grad=True)
        y = x + pm.Tensor(np.array([1.0, 1.0, 1.0]))
        y.detach_graph()
        self.assertIsNone(y._creator)
        # Backward from y should not flow into x
        y.backward()
        self.assertIsNone(x.grad)

    def test_fwd_context_freed_after_backward(self):
        x = pm.Tensor(np.array([0.5, 1.0, 2.0]), requires_grad=True)
        y = mach.log2(x)             # node caches context (including "out")
        node = y._creator
        self.assertIsNotNone(node)
        self.assertIsNotNone(node.fwd_ctx)     # lazily created dict
        y.backward()
        # After backward, context should be freed by engine
        self.assertIsNone(node._fwd_cache)


if __name__ == "__main__":
    ut.main(verbosity=2)
