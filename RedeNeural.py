import numpy as np
import random
import pickle
from tqdm.auto import tqdm, trange


class RedeNeural:
    def __init__(self, tamanhos):
        self.ncamadas = len(tamanhos)
        self.tamanhos = tamanhos
        self.bias  = [np.random.uniform(-1, 1, (y, 1)) for y in tamanhos[1:]]
        self.pesos = [np.random.uniform(-1, 1, (y, x)) for x, y in zip(tamanhos[:-1], tamanhos[1:])]
    
    def sigmoide(self, z):
        return 1. / (1. + np.exp(-z))
    
    def sigmoide_prim(self, z):
        return self.sigmoide(z) * (1 - self.sigmoide(z))
    
    def feedForward(self, a):
        for b, w in zip(self.bias, self.pesos):
            a = self.sigmoide(np.dot(w, a) + b)
        return a
        
    def SGD(self, treino, epocas, tamanho_lote, eta, teste=None):
        #import ipdb; ipdb.set_trace()
        treino = list(treino)
        n = len(treino)
        
        if teste:
            teste = list(teste)
            n_teste = len(teste)
        
        for j in trange(epocas, desc="Progresso: "):
            random.shuffle(treino)
            lotes = [treino[k:k+tamanho_lote] for k in range(0, n, tamanho_lote)]
            
            for lote in lotes:
                self.atualiza_lote(lote, eta)
                
            if teste:
            #    print("Época {} : {}/{}".format(j, self.avalia(teste), n_teste));
                tqdm.write("Época %i : %i" % j, self.avalia(teste),n_teste)
            #else:
            #    print("Época {} finalizada".format(j))
                tqdm.write("Época %i" % j)
                
    def atualiza_lote(self, lote, eta):
        nabla_b = [np.zeros(b.shape) for b in self.bias]
        nabla_w = [np.zeros(w.shape) for w in self.pesos]
        
        for x, y in lote:
            delta_nabla_b, delta_nabla_w = self.backprop(x, y)
            nabla_b = [nb+dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
            nabla_w = [nw+dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]
            
        self.pesos = [w-(eta/len(lote))*nw for w, nw in zip(self.pesos, nabla_w)]
        self.bias  = [b-(eta/len(lote))*nb for b, nb in zip(self.bias, nabla_b)]
        
    def backprop(self, x, y):
        nabla_b = [np.zeros(b.shape) for b in self.bias]
        nabla_w = [np.zeros(w.shape) for w in self.pesos]
        
        # Feedforward
        ativacao = x
        
        # Lista para armazenar todas as ativações, camada por camada
        ativacoes = [x]
        
        # Lista par armazenar todos os vetores z, camada por camada
        zs = []
        
        for b, w in zip(self.bias, self.pesos):
            z = np.dot(w, ativacao) + b
            zs.append(z)
            ativacao = self.sigmoide(z)
            ativacoes.append(ativacao)
        
        # Backward pass
        delta = self.derivada_custo(ativacoes[-1], y) * self.sigmoide_prim(zs[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = np.dot(delta, ativacoes[-2].transpose())
        
        for l in range(2, self.ncamadas):
            z = zs[-l]
            sp = self.sigmoide_prim(z)
            delta = np.dot(self.pesos[-l+1].transpose(), delta) * sp
            nabla_b[-l] = delta
            nabla_w[-l] = np.dot(delta, ativacoes[-l-1].transpose())
        return (nabla_b, nabla_w)
    
    def avalia(self, teste):
        if((type(teste[0][1]) == np.ndarray)):
            resultado_teste = [(np.argmax(self.feedForward(x)), np.argmax(y)) for (x, y) in teste]
        else:
            resultado_teste = [(np.argmax(self.feedForward(x)), y) for (x, y) in teste]
        return sum(int(x == y) for (x, y) in resultado_teste)

    def derivada_custo(self, output_activations, y):
        return (output_activations-y)
    
    @staticmethod
    def save_object(obj, filename):
        with open(filename, 'wb') as output:  # Overwrites any existing file.
            pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
    
    @staticmethod
    def load_object(filename):
        f = open(filename, 'rb')
        return pickle.load(f)
