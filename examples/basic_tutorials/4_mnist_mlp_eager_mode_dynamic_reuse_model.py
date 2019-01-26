import tensorflow as tf
## enable eager mode
tf.enable_eager_execution()

import time
import numpy as np
import tensorlayer as tl
from tensorlayer.layers import Input, Dense, Dropout
from tensorlayer.models import Model
import tensorflow.contrib.eager as tfe

## enable debug logging
tf.logging.set_verbosity(tf.logging.DEBUG)
tl.logging.set_verbosity(tl.logging.DEBUG)

## prepare MNIST data
X_train, y_train, X_val, y_val, X_test, y_test = tl.files.load_mnist_dataset(shape=(-1, 784))

## define the network
class CustomModelHidden(Model):

    def __init__(self):
        super(CustomModelHidden, self).__init__()

        self.innet = Input([None, 784])
        self.dropout1 = Dropout(keep=0.8)(self.innet)
        self.dense1 = Dense(n_units=800, act=tf.nn.relu)(self.dropout1)
        self.dropout2 = Dropout(keep=0.8)(self.dense1)
        self.dense2 = Dense(n_units=800, act=tf.nn.relu)(self.dropout2)
        self.dropout3 = Dropout(keep=0.8)(self.dense2)

    def forward(self, x):
        z = self.innet(x)
        z = self.dropout1(z)
        z = self.dense1(z)
        z = self.dropout2(z)
        z = self.dense2(z)
        z = self.dropout3(z)
        return z

class CustomModelOut(Model):

    def __init__(self):
        super(CustomModelOut, self).__init__()

        self.innet = Input([None, 800])
        self.dense3 = Dense(n_units=10, act=tf.nn.relu)(self.innet)
        self.dense4 = Dense(n_units=10)(self.innet)

    def forward(self, x, foo=0):
        z = self.innet(x)
        if foo == 0:
            out = self.dense3(z)
        else:
            out = self.dense4(z)
            out.outputs = tf.nn.relu(out.outputs)
        return out


# NOTE: using previous defined model is different in dynamic network
# a dynamic network cannot be converted into Layer because the inputs and outputs are unknown until forwarding
# therefore, you may reuse a previous defined model in the following way

MLP1 = CustomModelHidden()
MLP2 = CustomModelOut()
# MLP.print_layers()
# MLP.print_weights()
# print(MLP.outputs.outputs)

## start training
n_epoch = 500
batch_size = 500
print_freq = 5
train_weights = MLP1.weights + MLP2.weights
optimizer = tf.train.AdamOptimizer(learning_rate=0.0001)

## the following code can help you understand SGD deeply
for epoch in range(n_epoch):  ## iterate the dataset n_epoch times
    start_time = time.time()
    ## iterate over the entire training set once (shuffle the data via training)

    for X_batch, y_batch in tl.iterate.minibatches(X_train, y_train, batch_size, shuffle=True):

        MLP1.train()  # enable dropout
        MLP2.train()

        with tf.GradientTape() as tape:
            ## compute outputs
            _hidden = MLP1(X_batch).outputs
            _logits = MLP2(_hidden, foo=1).outputs
            ## compute loss and update model
            _loss = tl.cost.cross_entropy(_logits, y_batch, name='train_loss')

        grad = tape.gradient(_loss, train_weights)
        optimizer.apply_gradients(zip(grad, train_weights))

    ## use training and evaluation sets to evaluate the model every print_freq epoch
    if epoch + 1 == 1 or (epoch + 1) % print_freq == 0:

        MLP1.eval()  # disable dropout
        MLP2.eval()

        print("Epoch {} of {} took {}".format(epoch + 1, n_epoch, time.time() - start_time))

        train_loss, train_acc, n_iter = 0, 0, 0
        for X_batch, y_batch in tl.iterate.minibatches(X_train, y_train, batch_size, shuffle=False):
            _hidden = MLP1(X_batch).outputs
            _logits = MLP2(_hidden, foo=1).outputs
            train_loss += tl.cost.cross_entropy(_logits, y_batch, name='eval_loss')
            train_acc += np.mean(np.equal(np.argmax(_logits, 1), y_batch))
            n_iter += 1
        print("   train foo=1 loss: {}".format(train_loss / n_iter))
        print("   train foo=1 acc:  {}".format(train_acc / n_iter))

        val_loss, val_acc, n_iter = 0, 0, 0
        for X_batch, y_batch in tl.iterate.minibatches(X_val, y_val, batch_size, shuffle=False):
            _hidden = MLP1(X_batch).outputs
            _logits = MLP2(_hidden, foo=1).outputs
            val_loss += tl.cost.cross_entropy(_logits, y_batch, name='eval_loss')
            val_acc += np.mean(np.equal(np.argmax(_logits, 1), y_batch))
            n_iter += 1
        print("   val foo=1 loss: {}".format(val_loss / n_iter))
        print("   val foo=1 acc:  {}".format(val_acc / n_iter))

        val_loss, val_acc, n_iter = 0, 0, 0
        for X_batch, y_batch in tl.iterate.minibatches(X_val, y_val, batch_size, shuffle=False):
            _hidden = MLP1(X_batch).outputs
            _logits = MLP2(_hidden, foo=0).outputs
            val_loss += tl.cost.cross_entropy(_logits, y_batch, name='eval_loss')
            val_acc += np.mean(np.equal(np.argmax(_logits, 1), y_batch))
            n_iter += 1
        print("   val foo=0 loss: {}".format(val_loss / n_iter))
        print("   val foo=0 acc:  {}".format(val_acc / n_iter))

## use testing data to evaluate the model
MLP1.eval()
MLP2.eval()
test_loss, test_acc, n_iter = 0, 0, 0
for X_batch, y_batch in tl.iterate.minibatches(X_test, y_test, batch_size, shuffle=False):
    _hidden = MLP1(X_batch).outputs
    _logits = MLP2(_hidden, foo=0).outputs
    test_loss += tl.cost.cross_entropy(_logits, y_batch, name='test_loss')
    test_acc += np.mean(np.equal(np.argmax(_logits, 1), y_batch))
    n_iter += 1
print("   test foo=1 loss: {}".format(val_loss / n_iter))
print("   test foo=1 acc:  {}".format(val_acc / n_iter))
