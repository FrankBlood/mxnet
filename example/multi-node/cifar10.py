import sys
sys.path.insert(0, "../../python/")
import mxnet as mx

def data(data_dir, batch_size, num_parts=1, part_index=0):
    """return cifar10 iterator"""
    input_shape = (3,28,28)
    train = mx.io.ImageRecordIter(
        path_imgrec = data_dir + "/train.rec",
        mean_img    = data_dir + "/cifar_mean.bin",
        data_shape  = input_shape,
        batch_size  = batch_size,
        rand_crop   = True,
        rand_mirror = True,
        num_parts   = num_parts,
        part_index  = part_index)
    val = mx.io.ImageRecordIter(
        path_imgrec = data_dir + "/test.rec",
        mean_img    = data_dir + "/cifar_mean.bin",
        rand_crop   = False,
        rand_mirror = False,
        data_shape  = input_shape,
        batch_size  = batch_size)
    return (train, val)

# Basic Conv + BN + ReLU factory
def ConvFactory(data, num_filter, kernel, stride=(1,1), pad=(0, 0), act_type="relu"):
    conv = mx.symbol.Convolution(data=data, num_filter=num_filter, kernel=kernel, stride=stride, pad=pad)
    bn = mx.symbol.BatchNorm(data=conv)
    act = mx.symbol.Activation(data = bn, act_type=act_type)
    return act

# A Simple Downsampling Factory
def DownsampleFactory(data, ch_3x3):
    # conv 3x3
    conv = ConvFactory(data=data, kernel=(3, 3), stride=(2, 2), num_filter=ch_3x3, pad=(1, 1))
    # pool
    pool = mx.symbol.Pooling(data=data, kernel=(3, 3), stride=(2, 2), pool_type='max')
    # concat
    concat = mx.symbol.Concat(*[conv, pool])
    return concat

# A Simple module
def SimpleFactory(data, ch_1x1, ch_3x3):
    # 1x1
    conv1x1 = ConvFactory(data=data, kernel=(1, 1), pad=(0, 0), num_filter=ch_1x1)
    # 3x3
    conv3x3 = ConvFactory(data=data, kernel=(3, 3), pad=(1, 1), num_filter=ch_3x3)
    #concat
    concat = mx.symbol.Concat(*[conv1x1, conv3x3])
    return concat

def inception():
    data = mx.symbol.Variable(name="data")
    conv1 = ConvFactory(data=data, kernel=(3,3), pad=(1,1), num_filter=96, act_type="relu")
    in3a = SimpleFactory(conv1, 32, 32)
    in3b = SimpleFactory(in3a, 32, 48)
    in3c = DownsampleFactory(in3b, 80)
    in4a = SimpleFactory(in3c, 112, 48)
    in4b = SimpleFactory(in4a, 96, 64)
    in4c = SimpleFactory(in4b, 80, 80)
    in4d = SimpleFactory(in4c, 48, 96)
    in4e = DownsampleFactory(in4d, 96)
    in5a = SimpleFactory(in4e, 176, 160)
    in5b = SimpleFactory(in5a, 176, 160)
    pool = mx.symbol.Pooling(data=in5b, pool_type="avg", kernel=(7,7), name="global_pool")
    flatten = mx.symbol.Flatten(data=pool, name="flatten1")
    fc = mx.symbol.FullyConnected(data=flatten, num_hidden=10, name="fc1")
    softmax = mx.symbol.SoftmaxOutput(data=fc, name="loss")
    return softmax
