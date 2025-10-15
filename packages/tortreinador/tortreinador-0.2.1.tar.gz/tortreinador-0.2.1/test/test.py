import inspect
import pandas as pd
from torch.optim import Optimizer
from tortreinador import train
from tortreinador.utils.preprocessing import load_data, ScalerConfig
import torch
import torch.nn as nn
from tortreinador.models.MDN import mdn, Mixture, NLLLoss
from tortreinador.utils.plot import plot_line_2


df_chunk_0 = pd.read_parquet("D:\\Resource\\rockyExoplanetV3\\data_chunk_0.parquet")
df_chunk_1 = pd.read_parquet("D:\\Resource\\rockyExoplanetV3\\data_chunk_1.parquet")

df_all = pd.concat([df_chunk_0, df_chunk_1])

input_parameters = [
    'Mass',
    'Radius',
    'FeMg',
    'SiMg',
]


output_parameters = [
    'WRF',
    'MRF',
    'CRF',
    'WMF',
    'CMF',
    'CPS',
    'CTP',
    'k2'
]

# t_loader, v_loader, test_x, test_y, s_x, s_y = load_data(data=df_all, input_parameters=input_parameters,
#                                                          output_parameters=output_parameters,
#                                                          if_normal=True, if_shuffle=True, batch_size=1024, feature_range=(0, 1), n_workers=8, add_noise=True, error_rate=[0.14, 0.04, 0.12, 0.13], only_noise=True, normal_y=False)

t_loader, v_loader, test_x, test_y, s_x, s_y = load_data(data=df_all, input_parameters=input_parameters,
                                                         output_parameters=output_parameters,
                                                         normal=ScalerConfig(on=True, method='standard', normal_y=True), if_shuffle=True, batch_size=1024, n_workers=8, add_noise=True, error_rate=[0.14, 0.04, 0.12, 0.13], only_noise=True)


trainer = train.TorchTrainer(epoch=10)

model = mdn(len(input_parameters), len(output_parameters), 10, 256)
criterion = NLLLoss()
pdf = Mixture()
optim = torch.optim.Adam(model.parameters(), lr=0.0001984)

t_l, v_l, val_r2, train_r2, mse = trainer.fit_for_MDN(t_loader, v_loader, criterion, model=model, mixture=pdf,
                                                      model_save_path='D:\\Resource\\MDN\\', optim=optim, best_r2=0.9)


result_pd = pd.DataFrame()
result_pd['epoch'] = range(10)
result_pd['train_r2_avg'] = train_r2
result_pd['val_r2_avg'] = val_r2

plot_line_2(y_1='train_r2_avg', y_2='val_r2_avg', df=result_pd, fig_size=(10, 6), output_path="D:\\PythonProject\\RebuildProject\\Rock\\imgs\\Test_TrainValR2.png", dpi=300)


test_dict = {
               'loss': (1.0001, '.4f'),
               'loss_avg': (2.0002, '.4f'),
               'r2': (0.9804, '.4f'), 'lr_milestone': {'stone_list': [0, 1, 2], 'gamma': 0.7}
           }

test_value = test_dict['loss'][0]


class testClass:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v[0])

        if 'loss' in self.__dict__:
            print(getattr(self, 'loss'))


t = testClass(**test_dict)


def test_function():
    return [0, 1, 't']


def test_function2(*args):
    for i in args:
        print(i)


test_list = [0, 1, 't']
test_function2(*test_function())
isinstance(optim, Optimizer)


m = nn.MSELoss()
parameters = inspect.getfullargspec(m.__init__).args
parameter_name = parameters[0]

"""
    Combine Conv1d and resnet
"""

conv1 = nn.Conv1d(in_channels=12, out_channels=3, kernel_size=3, padding=1).float()
from torchvision.models import ResNet18_Weights

resnet18 = models.resnet18(weights=ResNet18_Weights.DEFAULT)

for param in resnet18.parameters():
    param.requires_grad = False
num_ftrs = resnet18.fc.in_features
resnet18.fc = nn.Linear(num_ftrs, 3)


class Transfer_resnet(nn.Module):
    def __init__(self, resnet, conv1D):
        super(Transfer_resnet, self).__init__()
        self.conv1D = conv1D
        self.bn = nn.BatchNorm2d(3)
        self.relu = nn.ReLU()
        self.resnet = resnet

    def forward(self, x):
        x = self.conv1D(x)
        x = self.relu(x)
        x1 = x.permute(-1, 1, 0)
        x1 = x1.unsqueeze(-1)
        x1 = self.resnet(x1)
        return x1

