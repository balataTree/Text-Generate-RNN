# -*- coding: utf-8 -*-

import os
import io
import sys
import time
import tensorflow as tf
import numpy as np
from net import Net
from data import Data

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

num_units = 128
num_layer = 2
batch_size = 16
num_step = 100 * 10000
learning_rate = 0.001

with open('setting.ini', 'a') as f:
    time_ = time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime())
    s = 'num_layers: %d, layers_size: %d, batch_size: %d, lr: %.6f\n' % (
        num_layer, num_units, batch_size, learning_rate)
    f.write(time_ + s)

data_dir = 'data/'
input_file = 'tang'
vocab_file = 'vocab.pkl'
tensor_file = 'tensor.npy'

model_dir = 'model'
if not os.path.exists(model_dir):
    os.mkdir(model_dir)

summary_dir = 'summary'
if not os.path.exists(summary_dir):
    os.mkdir(summary_dir)

summary_name = str(int(time.time()))
summary_savepath = os.path.join(summary_dir, summary_name)
os.mkdir(summary_savepath)

data = Data(data_dir, input_file, vocab_file, tensor_file, batch_size)
model = Net(data, num_units, num_layer, batch_size)

with tf.Session() as sess:
    writer = tf.summary.FileWriter(summary_savepath, sess.graph)
    tf.global_variables_initializer().run()
    saver = tf.train.Saver(tf.global_variables(), max_to_keep=5)    

    for step in range(num_step):
        inputs, labels, seq_len = data.get_batches()
        feed = {
            model.inputs: inputs,
            model.targets: labels,
            model.seq_len: seq_len,
            model.learning_rate: learning_rate,
            model.keep_prob: 0.5
        }
        fetches = [model.pre, model.loss, model.merged_summary, model.train_op]
        pre, loss, summary, _ = sess.run(fetches, feed_dict=feed)
        writer.add_summary(summary, step)

        if step % 100 == 0:
            original = ''.join(list(map(data.id2char, inputs[0][:seq_len[0]])))
            predict = ''.join(list(map(data.id2char, pre[0][:seq_len[0]])))            
            print('step: %d, loss: %.4f, lr: %.6f' % (step, loss, learning_rate))
            print('original: %s' % (original))
            print('predict: %s\n' % (predict))
            with open('train_step.txt', 'a') as f:
                time_ = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                text = '%s, loss: %.4f, step: %d\n%s\n\n' % (time_, loss, step, predict)
                f.write(text)

        if step % 1000 == 0:
            model_name = os.path.join(model_dir, 'model_loss_%.4f.ckpt' % (loss))
            saver.save(sess, model_name, global_step=step)    
            print('save model in step: %d' % (step))

        if step % 2000 == 0:
            learning_rate = max(learning_rate*0.95, 0.000001)