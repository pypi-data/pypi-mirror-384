import time
import warnings
import pprint
from dpplgngr.utils.utils_data_graph import *
from train.vae_train import *
from train.opts import *
warnings.filterwarnings("ignore")


def get_options():
    opt = Options()
    opt = opt.initialize()
    return opt


def timelog(func):
    print("This is a time logger.")

    def printtime(*args, **argv):
        t1 = time.time()
        print("Start time: {}".format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t1))))
        returns = func(*args, **argv)
        t2 = time.time()
        print("End time: {}".format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t2))))
        print("Time consumption: {}s".format(t2-t1))
        return returns
    return printtime


if __name__ == "__main__":
    opt = get_options()

    opt.gpu = '0'
    opt.max_epochs = 2
    opt.logits = 1
    opt.batch_size = 1
    opt.data_dir = "./data/ENZYMES_20-50_res.graphs"
    ## 正式训练时收起 }
    os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpu
    print('=========== OPTIONS ===========')
    pprint.pprint(vars(opt))
    print(' ======== END OPTIONS ========\n\n')

    train_adj_mats, test_adj_mats, train_attr_vecs, test_attr_vecs = load_data(
        DATA_FILEPATH=opt.data_dir)
    with torch.autograd.set_detect_anomaly(True):
        trained_model = train(
            opt=opt,
            train_adj_mats=train_adj_mats
        )
    # todo: write testing process after all training process.
    print("success!")