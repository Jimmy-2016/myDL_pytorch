
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from torchvision import models, transforms, utils
from PIL import Image
import requests

transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
]

)


def download(url, fname):
    response = requests.get(url)
    with open(fname, "wb") as f:
        f.write(response.content)


# Downloading the image
download("https://specials-images.forbesimg.com/imageserve/5db4c7b464b49a0007e9dfac/960x0.jpg?fit=scale", "input.jpg")

# Opening the image
img = Image.open('input.jpg')

# img = Image.open(str('./1.jpg'))
plt.imshow(img)

## load the model

model = models.resnet18(pretrained=True)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
print(model)
print(device)


##
model_weights =[]
conv_layers = []

model_children = list(model.children())
counter = 0
for i in range(len(model_children)):
    if type(model_children[i]) == nn.Conv2d:
        counter += 1
        model_weights.append(model_children[i].weight)
        conv_layers.append(model_children[i])
    elif type(model_children[i]) == nn.Sequential:
        for j in range(len(model_children[i])):
            for child in model_children[i][j].children():
                if type(child) == nn.Conv2d:
                    counter += 1
                    model_weights.append(child.weight)
                    conv_layers.append(child)
print(f"Total convolution layers: {counter}")
print("conv_layers")

##
# preprocess the image
X = transforms(img)
X = X.unsqueeze(0)

# we would run the model in evaluation mode
model.eval()

# we need to find the gradient with respect to the input image, so we need to call requires_grad_ on it
X.requires_grad_()

'''
forward pass through the model to get the scores, note that VGG-19 model doesn't perform softmax at the end
and we also don't need softmax, we need scores, so that's perfect for us.
'''

scores = model(X)

# Get the index corresponding to the maximum score and the maximum score itself.
score_max_index = scores.argmax()
score_max = scores[0, score_max_index]

'''
backward function on score_max performs the backward pass in the computation graph and calculates the gradient of 
score_max with respect to nodes in the computation graph
'''
score_max.backward()

grads = []
names = []
for layer in conv_layers:
    grads.append(torch.max(layer.weight.grad.abs(), dim=0))
    names.append(str(layer))
print(len(grads))
# for feature_map in grads:
#     print(feature_map.shape)


'''
Saliency would be the gradient with respect to the input image now. But note that the input image has 3 channels,
R, G and B. To derive a single class saliency value for each pixel (i, j),  we take the maximum magnitude
across all colour channels.
'''
saliency, _ = torch.max(X.grad.data.abs(), dim=1)

# code to plot the saliency map as a heatmap
plt.imshow(saliency[0], cmap=plt.cm.hot)
plt.axis('off')



##

for i in range(len(grads)):
    plt.figure()
    plt.imshow(grads[i][0], cmap=plt.cm.hot)

plt.show()