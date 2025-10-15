import torch, torch.nn as nn



class GatedConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, groups=1):
        super(GatedConv, self).__init__()
        self.layer_f = nn.Conv2d(
            in_channels, out_channels, kernel_size, stride=stride, padding=padding, dilation=1, groups=groups
        )
        self.layer_g = nn.Conv2d(
            in_channels, out_channels, kernel_size, stride=stride, padding=padding, dilation=1, groups=groups
        )

    def forward(self, x):
        f = self.layer_f(x)
        g = torch.sigmoid(self.layer_g(x))
        return f * g



def supported_hyperparameters():
    return {'lr','momentum'}

class Net(nn.Module):
    def __init__(self, in_shape: tuple, out_shape: tuple, prm: dict, device: torch.device) -> None:
        super().__init__()
        self.device = device
        self.in_channels = in_shape[1]
        self.image_size = in_shape[2]
        self.num_classes = out_shape[0]
        self.learning_rate = prm['lr']
        self.momentum = prm['momentum']

        self.features = self.build_features()
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(self._last_channels, self.num_classes)

    def build_features(self):
        layers = []
        layers.append(GatedConv(self.in_channels, 64, 3, padding=1))
        layers.append(nn.BatchNorm2d(64))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(3, stride=2, padding=1))

        layers.append(GatedConv(64, 128, 3, padding=1))
        layers.append(nn.BatchNorm2d(128))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(3, stride=2, padding=1))

        layers.append(GatedConv(128, 256, 3, padding=1))
        layers.append(nn.BatchNorm2d(256))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.MaxPool2d(3, stride=2, padding=1))

        self._last_channels = 256
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)

    def train_setup(self, prm):
        self.to(self.device)
        self.criteria = nn.CrossEntropyLoss().to(self.device)
        self.optimizer = torch.optim.SGD(
            self.parameters(), lr=self.learning_rate, momentum=self.momentum)

    def learn(self, train_data):
        self.train()
        for inputs, labels in train_data:
            inputs, labels = inputs.to(self.device), labels.to(self.device)
            self.optimizer.zero_grad()
            outputs = self(inputs)
            loss = self.criteria(outputs, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(self.parameters(), 3)
            self.optimizer.step()