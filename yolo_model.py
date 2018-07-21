import keras
from keras.layers import Conv2D,Input,BatchNormalization,\
    LeakyReLU,Add,GlobalAveragePooling2D,Dense,Activation
from keras.models import Model
from keras.optimizers import Adam
from keras import backend as K
from keras.preprocessing.image import load_img
from keras.losses import categorical_crossentropy
import tensorflow as tf
import numpy as np
from utils import preprocess,softmax

class Basic_Conv():
    def __init__(self,filters,kernel_size,strides=(1,1),batch_normalize=True,
                 pad='same',activation='leaky'):
        self.filters = filters
        self.kernel_size = kernel_size
        self.strides = strides
        self.batch_normalize = batch_normalize
        self.pad = pad
        self.activation = activation
    def __call__(self, food):
        shit = Conv2D(filters=self.filters,
                      kernel_size=self.kernel_size,
                      strides=self.strides,padding=self.pad)(food)
        if self.activation == 'leaky':
            shit = LeakyReLU(alpha=0.1)(shit)
        shit = BatchNormalization()(shit)

        return shit
class Basic_Res():
    def __init__(self,activation='linear'):
        self.activation = activation
    def __call__(self, shitA,shitB):
        shit = Add()([shitA,shitB])
        if self.activation == "linear":
            shit = Activation(self.activation)(shit)
        return shit

class YOLO_V3():
    def __init__(self):
        pass
    def construct_model(self,output_units=1000):

        inputs = Input(shape=(256,256,3))
        shits = []
        shits.append(Basic_Conv(filters=32,kernel_size=3)(inputs))

        shits.append(Basic_Conv(filters=64, kernel_size=3, strides=(2, 2))(shits[-1]))

        shits.append(Basic_Conv(filters=32,kernel_size=1)(shits[-1]))
        shits.append(Basic_Conv(filters=64,kernel_size=3)(shits[-1]))
        shits.append(Basic_Res()(shits[-1],shits[-3]))

        shits.append(Basic_Conv(filters=128,kernel_size=3,strides=2)(shits[-1]))

        for i in range(2):
            shits.append(Basic_Conv(filters=64,kernel_size=1)(shits[-1]))
            shits.append(Basic_Conv(filters=128,kernel_size=3)(shits[-1]))
            shits.append(Basic_Res()(shits[-1],shits[-3]))

        # yolov3.cfg 113~283
        shits.append(Basic_Conv(filters=256,kernel_size=3,strides=2)(shits[-1]))
        for i in range(8):
            shits.append(Basic_Conv(filters=128,kernel_size=1)(shits[-1]))
            shits.append(Basic_Conv(filters=256,kernel_size=3)(shits[-1]))
            shits.append(Basic_Res()(shits[-1],shits[-3]))
        # yolov3.cfg 284~458
        shits.append(Basic_Conv(filters=512,kernel_size=3,strides=2)(shits[-1]))
        for i in range(8):
            shits.append(Basic_Conv(filters=256, kernel_size=1)(shits[-1]))
            shits.append(Basic_Conv(filters=512, kernel_size=3)(shits[-1]))
            shits.append(Basic_Res()(shits[-1], shits[-3]))
        # yolov3.cfg 459~547
        shits.append(Basic_Conv(filters=1024,kernel_size=3,strides=2)(shits[-1]))
        for i in range(4):
            shits.append(Basic_Conv(filters=512, kernel_size=1)(shits[-1]))
            shits.append(Basic_Conv(filters=1024, kernel_size=3)(shits[-1]))
            shits.append(Basic_Res()(shits[-1], shits[-3]))
        #
        shits.append(GlobalAveragePooling2D()(shits[-1]))
        logits = Dense(units=output_units)(shits[-1])
        self.model = Model(inputs=inputs,outputs=logits)
        self.model.summary()

    def train(self,train_generator,val_generator):

        loss_func = tf.losses.softmax_cross_entropy
        self.model.compile(optimizer=Adam(),loss=loss_func,metrics=['accuracy'])
        self.model.fit_generator(generator=train_generator,
                                 steps_per_epoch=800/8,
                                 epochs=2,
                                 validation_data=val_generator,
                                 validation_steps=280/8,class_weight='auto')
        self.model.save_weights('fl_model.h5')

    def load_weights(self,path):
        self.model.load_weights(path)
    def evaluate(self,generator):
        return self.model.evaluate_generator(generator)
    def predict(self,image_path,threshold=0.5):
        import random,os,cv2
        true_class = random.randint(0,16)
        target_folder = os.path.join(image_path,str(true_class))
        files = os.listdir(target_folder)
        fileindex = random.randint(0,len(files)-1)
        target_path = os.path.join(target_folder,files[fileindex])
        image = load_img(target_path,target_size=(256,256))

        np_image = np.array(image)
        image_for_cv2_show = np_image[:, :, ::-1].copy()

        image = np.expand_dims(np_image,axis=0)
        img = preprocess(image)
        result = self.model.predict(img)
        r = softmax(result)
        cv2.imshow('result', image_for_cv2_show)

        if np.max(r) > 0.5:
            index = np.argmax(r)
            pred_label = index
            if pred_label == true_class:
                message = " 🍺"
            else:
                message = " 💀"
            print('真值：',true_class,'预测值：',pred_label,message)
        else:
            print('真值：',true_class,'预测值：无'," 💀")
        cv2.waitKey(0)

def prepare_data():
    from keras.preprocessing.image import ImageDataGenerator
    train_datagen = ImageDataGenerator(rotation_range=30,
                                       width_shift_range=0.2,
                                       height_shift_range=0.2,
                                       shear_range=0.2,
                                       zoom_range=0.2,
                                       horizontal_flip=True,
                                       vertical_flip=True,
                                       preprocessing_function=lambda x:((x/255)-0.5)*2)
    val_datagen = ImageDataGenerator(rotation_range=30,
                                       width_shift_range=0.2,
                                       height_shift_range=0.2,
                                       shear_range=0.2,
                                       zoom_range=0.2,
                                       horizontal_flip=True,
                                       vertical_flip=True,
                                       preprocessing_function=lambda x:((x/255)-0.5)*2)
    # 默认的color_mode是RGB
    train_generator = train_datagen.flow_from_directory(directory='./flowers17/train/',
                                                        target_size=(256,256),batch_size=8)
    val_generator   = val_datagen.flow_from_directory(directory='./flowers17/validation/',
                                                      target_size=(256,256),batch_size=8)
    return train_generator,val_generator
if __name__ == "__main__":
    train_gen,val_gen =prepare_data()
    a = YOLO_V3()
    a.construct_model(output_units=17)
    a.train(train_gen,val_gen)
