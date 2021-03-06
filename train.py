from models import RnnGenerative
from utils import english_letters, word2Variable, makeTargetVariable, save_checkpoint, create_train_state, load_checkpoint
import torch
from torch import nn
from torch.autograd import Variable
from torch import optim
from datasets import startup_names, yield_dataset, people_names
from tqdm import tqdm
import os

n_length = len(english_letters) + 1
embedding_dim = 100
hidden_size = 150
batch_size = 512
use_gpu = torch.cuda.is_available()
generative = RnnGenerative(n_length, embedding_dim, hidden_size, unit='lstm', layer_num=2)
generative.init_hidden(batch_size, use_gpu)
if use_gpu:
    generative.cuda()
            

criterion = nn.NLLLoss()
optimizer = optim.Adam(generative.parameters(), lr=5e-3)
num_epochs = 60
model_filename = 'people-lstm-layer-2.model'
names = people_names()
generative.train()
if os.path.exists(model_filename):
    generative,optimizer,starting_epoch,_ = load_checkpoint(model_filename, generative, optimizer)
else:
    starting_epoch = 1
print('starting from epoch %d'%starting_epoch)
try:
    for epoch in range(starting_epoch, num_epochs+1):
        iterators = tqdm(yield_dataset(names, batch_size=batch_size))
        for data in iterators:
            input_words = word2Variable(data)
            target_words = makeTargetVariable(data)
            generative.init_hidden(batch_size, use_gpu)
            if use_gpu:
                input_words = input_words.cuda()
                target_words = target_words.cuda()
            generative.zero_grad()
            loss = 0
            for i in range(20):
                output = generative(input_words[i])
                loss += criterion(output, target_words[i])
            loss.backward(retain_graph=True)
            optimizer.step()
            iterators.set_description(desc='Epoch: {}/{} loss: {}'.format(epoch, num_epochs, loss.cpu().data.numpy()[0]))
        
        save_checkpoint(create_train_state(generative, epoch, optimizer), model_filename)
except KeyboardInterrupt:
    save_checkpoint(create_train_state(generative, epoch-1, optimizer), model_filename)
