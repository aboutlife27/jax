# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

from absl.testing import absltest
from absl.testing import parameterized

import numpy as onp

from jax import test_util as jtu
import jax.numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from examples import kernel_lsq
from examples import mnist_classifier
from examples import mnist_classifier_fromscratch
from examples import mnist_vae
from examples import resnet50
sys.path.pop()

from jax.config import config
config.parse_flags_with_absl()
FLAGS = config.FLAGS


def _CheckShapeAgreement(test_case, init_fun, apply_fun, input_shape):
  result_shape, params = init_fun(input_shape)
  rng = onp.random.RandomState(0)
  result = apply_fun(params, rng.randn(*input_shape).astype(dtype="float32"))
  test_case.assertEqual(result.shape, result_shape)


class ResNet50Test(jtu.JaxTestCase):

  @parameterized.named_parameters(
      {"testcase_name": "_input_shape={}".format(input_shape),
       "input_shape": input_shape}
      for input_shape in [(2, 20, 25, 2)])
  @jtu.skip_on_flag('jax_enable_x64', True)
  def testIdentityBlockShape(self, input_shape):
    init_fun, apply_fun = resnet50.IdentityBlock(2, (4, 3))
    _CheckShapeAgreement(self, init_fun, apply_fun, input_shape)

  @parameterized.named_parameters(
      {"testcase_name": "_input_shape={}".format(input_shape),
       "input_shape": input_shape}
      for input_shape in [(2, 20, 25, 3)])
  @jtu.skip_on_flag('jax_enable_x64', True)
  def testConvBlockShape(self, input_shape):
    init_fun, apply_fun = resnet50.ConvBlock(3, (2, 3, 4))
    _CheckShapeAgreement(self, init_fun, apply_fun, input_shape)

  @parameterized.named_parameters(
      {"testcase_name": "_num_classes={}_input_shape={}"
                        .format(num_classes, input_shape),
       "num_classes": num_classes, "input_shape": input_shape}
      for num_classes in [5, 10]
      for input_shape in [(224, 224, 3, 2)])
  @jtu.skip_on_flag('jax_enable_x64', True)
  def testResNet50Shape(self, num_classes, input_shape):
    init_fun, apply_fun = resnet50.ResNet50(num_classes)
    _CheckShapeAgreement(self, init_fun, apply_fun, input_shape)

  def testKernelRegressionGram(self):
    n, d = 100, 20
    rng = onp.random.RandomState(0)
    truth = rng.randn(d)
    xs = rng.randn(n, d)
    ys = np.dot(xs, truth)
    kernel = lambda x, y: np.dot(x, y)
    assert np.all(kernel_lsq.gram(kernel, xs) == np.dot(xs, xs.T))

  def testKernelRegressionTrainAndPredict(self):
    n, d = 100, 20
    rng = onp.random.RandomState(0)
    truth = rng.randn(d)
    xs = rng.randn(n, d)
    ys = np.dot(xs, truth)
    kernel = lambda x, y: np.dot(x, y)
    predict = kernel_lsq.train(kernel, xs, ys)
    assert np.allclose(predict(xs), ys, atol=1e-3)


if __name__ == "__main__":
  absltest.main()
