import tensorflow as tf
from hyperparams import Hyperparams as Hp
from modules import *


class Transformer(object):
    def __init__(self, char_embedding, hp: Hp, is_training=False):
        self.input_word = tf.placeholder(tf.int32, [None, hp.maxlen], name='input_word')
        self.input_pos1 = tf.placeholder(tf.int32, [None, hp.maxlen], name='input_pos1')
        self.input_pos2 = tf.placeholder(tf.int32, [None, hp.maxlen], name='input_pos2')
        self.input_y = tf.placeholder(tf.int32, [None, hp.num_classes], name='true_labels')

        with tf.name_scope("embedding"):
            with tf.name_scope("embedding"):
                word_embedding = tf.get_variable(initializer=char_embedding, name='word_embedding')
                pos_embedding = tf.get_variable('pos_embedding', [hp.pos_num, hp.pos_dim],
                                                initializer=tf.contrib.layers.xavier_initializer())

                self.embed_value = tf.concat(axis=2, values=[tf.nn.embedding_lookup(word_embedding, self.input_word),
                                                             tf.nn.embedding_lookup(pos_embedding, self.input_pos1),
                                                             tf.nn.embedding_lookup(pos_embedding, self.input_pos2)])

                # self.embed_value = tf.layers.dropout(self.embed_value,
                #                                      rate=hp.dropout_rate,
                #                                      training=tf.convert_to_tensor(is_training))

        with tf.name_scope("encoder"):
            self.enc = multihead_attention(queries=self.embed_value,
                                           keys=self.embed_value,
                                           num_units=hp.hidden_units,
                                           num_heads=hp.num_heads,
                                           dropout_rate=hp.dropout_rate,
                                           is_training=is_training,
                                           causality=False
                                           )
            self.enc = feedforward(self.enc, num_units=[4 * hp.hidden_units, hp.hidden_units])

        with tf.name_scope("outputs"):
            self.enc = tf.reshape(self.enc, shape=[-1, hp.maxlen*hp.hidden_units])
            self.logits = tf.layers.dense(self.enc, hp.num_classes, activation=None)
            self.pred_probability = tf.nn.softmax(self.logits, name="class_probability")
            self.preds = tf.argmax(self.pred_probability, axis=-1, name="class_prediction")

        with tf.name_scope("loss"):
            self.cross_entropy = tf.nn.softmax_cross_entropy_with_logits_v2(logits=self.logits, labels=self.input_y)
            self.l2_loss = tf.contrib.layers.apply_regularization(regularizer=tf.contrib.layers.l2_regularizer(0.0001),
                                                                  weights_list=tf.trainable_variables())
            self.final_loss = tf.reduce_mean(self.cross_entropy) + self.l2_loss
            tf.summary.scalar("loss", self.final_loss)

        with tf.name_scope("accuracy"):
            correct_predictions = tf.equal(self.preds, tf.argmax(self.input_y, 1))
            self.accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32), name='accuracy')
