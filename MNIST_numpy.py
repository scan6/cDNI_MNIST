# -*- coding: utf-8 -*-
"""
Created on Fri Jan 26 22:27:17 2018

@author: pig84
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import MinMaxScaler
import time

def load_data(file_name):
    df = pd.read_csv(file_name)
    X = df.drop(['label'], axis = 1).values.astype(np.float64)
    #normalize X
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)
    
    y = df['label'].values.reshape(-1, 1)
    enc = OneHotEncoder()
    y = enc.fit_transform(y).toarray()
    return train_test_split(X, y, test_size = 0.2, random_state = 1)

def sigmoid(x):
    np.seterr( over='ignore' ) #ignore sigmoid overflow
    return 1 / (1 + np.exp(-x))

def sigmoid_out2deriv(out):
    return out * (1 - out)

def stable_softmax(X):
    n, d = X.shape
    exps = np.exp(X - np.max(X))
    exps_sum = np.sum(exps, axis = 1)
    for _ in range(n):
        exps[_, :] = exps[_, :] / exps_sum[_]
    return exps

def cross_entropy(logits, labels, epsilon = 1e-12):
    logits = np.clip(logits, epsilon, 1. - epsilon)
    ce = -labels*np.log(logits + 1e-9)
    return ce

class network(object):
    
    def __init__(self,input_dim, output_dim, nonlin = None, nonlin_deriv = None, alpha = 0.001):
        
        self.weights = np.random.randn(input_dim, output_dim)
        self.bias = np.random.randn(output_dim)
    
        self.nonlin = nonlin
        self.nonlin_deriv = nonlin_deriv
        self.alpha = alpha
    
    def forward_pass(self, inputs):
        self.inputs = inputs
        if self.nonlin == None :
            self.outputs = self.inputs.dot(self.weights) + self.bias
        else:
            self.outputs = self.nonlin(self.inputs.dot(self.weights) + self.bias)
        return self.outputs
    
    def backward_pass(self,true_gradient):
        if self.nonlin_deriv == None:
            grad = true_gradient
        else:
            grad = true_gradient * self.nonlin_deriv(self.outputs)
        
        pre_grad = grad.dot(self.weights.T)
        self.weights -= self.inputs.T.dot(grad) * self.alpha
        self.bias -= np.average(grad,axis=0) * self.alpha
        return pre_grad

if __name__ == '__main__':
    print('Start')
    X_train, X_test, y_train, y_test = load_data('mnist_train.csv')
    n, d = X_train.shape
    batch_size = 200
    iterations = 10
    np.random.seed(1)
    
    layer_1 = network(d, 256, nonlin = sigmoid, nonlin_deriv = sigmoid_out2deriv)
    layer_2 = network(256, 256, nonlin = sigmoid, nonlin_deriv = sigmoid_out2deriv)
    layer_3 = network(256, 256, nonlin = sigmoid, nonlin_deriv = sigmoid_out2deriv)
    layer_4 = network(256, 256, nonlin = sigmoid, nonlin_deriv = sigmoid_out2deriv)
    layer_5 = network(256, 256, nonlin = sigmoid, nonlin_deriv = sigmoid_out2deriv)
    layer_6 = network(256, 10, nonlin = None, nonlin_deriv = None)
    
    results = []
    start_time = time.time()
    for iters in range(iterations):
        for batch in range(int (n / batch_size)):
            batch_xs = X_train[(batch*batch_size) : (batch+1)*batch_size]
            batch_ys = y_train[(batch*batch_size) : (batch+1)*batch_size]
            
            a1 = layer_1.forward_pass(batch_xs)
            a2 = layer_2.forward_pass(a1)
            a3 = layer_3.forward_pass(a2)
            a4 = layer_4.forward_pass(a3)
            a5 = layer_5.forward_pass(a4)
            z6 = layer_6.forward_pass(a5)
            a6 = stable_softmax(z6)
            ce = cross_entropy(logits = a6, labels = batch_ys)
            
            if batch % 10 == 0:
                loss = np.sum(ce)/200
                results.append(loss)
                print(loss)
            
            layer_6_delta = a6 - batch_ys
            layer_5_delta = layer_6.backward_pass(layer_6_delta)
            layer_4_delta = layer_5.backward_pass(layer_5_delta)
            layer_3_delta = layer_4.backward_pass(layer_4_delta)
            layer_2_delta = layer_3.backward_pass(layer_3_delta)
            layer_1_delta = layer_2.backward_pass(layer_2_delta)
            layer_1.backward_pass(layer_1_delta)
    end_time = time.time()
    print("It cost %f sec" % (end_time-start_time))
    np.savetxt('normal_results.csv', np.asarray(results), delimiter=',')