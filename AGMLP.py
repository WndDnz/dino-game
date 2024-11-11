from tqdm.autonotebook import tqdm, trange
import RedeNeural
import random
import operator
import numpy as np

"""
A classe RNA_AG usa um algoritmo genético para treinar uma RNA do tipo feed-forward
"""


class RNA_AG:

    def __init__(
        self,
        configRede,
        treino,
        eta,
        nIndividuos,
        geracoes,
        taxaMutacao=0.01,
        elite=None,
        teste=None,
    ):
        """
        No construtor, passamos a configuração das Redes Neurais, o arquivo de dados de treinamento,
        o número de indíviduos de cada geração, a taxa de mutação, o número de indivíduos a serem
        promovidos, caso queira usar elitismo, e um arquivo de teste opcional
        """
        self.configRede = configRede
        self.treino = treino
        self.eta = eta
        self.nIndividuos = nIndividuos
        self.geracoes = geracoes
        self.taxaMutacao = taxaMutacao
        self.elite = elite, trange
        self.tamElite = int(nIndividuos * elite)
        self.teste = teste

    def iniciaPopulacao(self, nIndividuos=None):
        """
        Aqui, iniciamos nossa população. Cada indivíduo será uma RNA com a configuração passada no
        construtor da classe.
        """
        if nIndividuos is not None and nIndividuos > 0:
            return [RedeNeural.RedeNeural(self.configRede) for i in range(nIndividuos)]
        else:
            return [
                RedeNeural.RedeNeural(self.configRede) for i in range(self.nIndividuos)
            ]

    def ranquearIndividuos(self, populacao):
        """
        Essa é a nossa função de fitness. Ranqueamos cada indivíduo usando o método avalida da rede
        implementada, que devolve o número total de acertos (amostras corretamente classificadas)
        """
        fitness = {key: specimen[0] for (key, specimen) in enumerate(populacao)}
        return sorted(fitness.items(), key=operator.itemgetter(1), reverse=True)

    def selecao(self, popRanqueada, tamElite, numPartTorneio=0.2):
        """
        Este método implementa a seleção por torneio. Uma fração da população é sorteada aleatoriamente
        e o melhor indíviduo do grupo é promovido para o grupo de reprodução. Note que retornamos uma lista
        com os índices dos indivíduos sorteados.
        """
        res = []
        tam = len(popRanqueada) - tamElite if tamElite else len(popRanqueada)
        numTorneio = int(len(popRanqueada) * numPartTorneio)
        if tamElite:
            for i in range(tamElite):
                res.append(popRanqueada[i][0])
        res += [
            max(random.sample(popRanqueada, numTorneio), key=operator.itemgetter(1))[0]
            for i in range(tam)
        ]
        random.shuffle(res)
        return res

    def grupoDeReproducao(self, populacao, selecao):
        """
        Aqui, apenas montamos uma lista com os indivíduos que foram selecinados no torneio.
        """
        return [populacao[indice][1] for indice in selecao]

    def acasala(self, pai1, pai2):
        """
        A função acasala aplica o operador genético BLX-alpha. Esse operador gera
        um filho seguindo a equação F = P1 + \beta * (P2 - P1), onde \beta
        """
        b1 = pai1.bias.copy()
        b2 = pai2.bias.copy()
        w1 = pai1.pesos.copy()
        w2 = pai2.pesos.copy()

        filho = RedeNeural.RedeNeural(self.configRede)

        alpha = 0.1
        beta = np.random.uniform(-alpha, 1 + alpha)
        for i in range(pai1.ncamadas - 1):
            # shapeOrig = b1[i].shape
            bias_filho = b1[i] + beta * (b2[i] - b1[i])

            # shapeOrig = w1[i].shape
            # beta = np.random.uniform(-alpha, 1 + alpha, shapeOrig)
            pesos_filho = w1[i] + beta * (w2[i] - w1[i])

            filho.bias[i] = bias_filho
            filho.pesos[i] = pesos_filho

        return filho

    def acasala2(self, pai1, pai2):
        """
        A função acasala aplica o operador genético de crossover. Consideramos que cada indivíduo possui
        dois cromossomos, a lista de bias e a lista de pesos de cada camada da RNA. Fazemos o crossover
        escolhendo aleatoriamente um segmento da fita de DNA dos pais para ser cortado e trocado entre
        os filhos.
        """
        b1 = pai1.bias.copy()
        b2 = pai2.bias.copy()
        w1 = pai1.pesos.copy()
        w2 = pai2.pesos.copy()

        filho = RedeNeural.RedeNeural(self.configRede)

        for i in range(pai1.ncamadas - 1):
            shapeOrig = b1[i].shape
            cortes = (
                int(random.random() * b1[i].shape[0]),
                int(random.random() * b1[i].shape[0]),
            )
            com, fim = (min(cortes), max(cortes))

            genep11 = b1[i].ravel()[:com]
            # filhoP1i = b1[i].ravel()[com:fim]
            genep12 = b1[i].ravel()[fim:]

            # filhoP2c = b2[i].ravel()[:com]
            genep2 = b2[i].ravel()[com:fim]
            # filhoP2f = b2[i].ravel()[fim:]

            biasfilho = np.concatenate((genep11, genep2, genep12))
            biasfilho = biasfilho.reshape(shapeOrig)

            # Cromossomo do peso
            shapeOrig = w1[i].shape

            cw1 = w1[i].ravel()
            cw2 = w2[i].ravel()

            cortes = (
                int(random.random() * cw1.shape[0]),
                int(random.random() * cw1.shape[0]),
            )
            com, fim = (min(cortes), max(cortes))

            filhoP1wc = cw1[:com]
            # filhoP1wi = cw1[com:fim]
            filhoP1wf = cw1[fim:]

            # filhoP2wc = cw2[:com]
            filhoP2wi = cw2[com:fim]
            # filhoP2wf = cw2[fim:]

            pesosfilho = np.concatenate((filhoP1wc, filhoP2wi, filhoP1wf))
            pesosfilho = pesosfilho.reshape(shapeOrig)

            filho.bias[i] = biasfilho
            filho.pesos[i] = pesosfilho
        return filho

    def acasalaPppulacao(self, pais, tamElite):
        """
        Aplicamos o crossover sobre todos os indivíduos para gerar a próxima geração.
        """
        filhos = []
        tam = len(pais) - tamElite if tamElite else len(pais)
        pool = random.sample(pais, len(pais))

        if tamElite:
            filhos = [pais[i] for i in range(tamElite)]
        filhos += [self.acasala(pool[i], pool[len(pais) - i - 1]) for i in range(tam)]
        return filhos

    def aplicaMutacao(self, individuo, taxaMutacao):
        """
        Aplicamos a mutação, variando conforme a taxa, valores de cada cromossomo.
        """
        camadas = individuo.ncamadas - 1
        for c in range(camadas):
            for b in range(individuo.bias[c].shape[0]):
                if random.random() < taxaMutacao:
                    # v = np.array([random.random()])
                    individuo.bias[c][b][0] = np.random.randn()
            for w in range(individuo.pesos[c].shape[0]):
                if random.random() < taxaMutacao:
                    ind = random.randint(0, individuo.pesos[c][w].shape[0] - 1)
                    individuo.pesos[c][w][ind] = np.random.randn()
        return individuo

    def mutacaoPopulacao(self, populacao, taxaMutacao):
        """
        Agora, aplicamos a mutação à população gerada pelo crossover.
        """
        return [self.aplicaMutacao(individuo, taxaMutacao) for individuo in populacao]

    def proximaGeracao(self, geracaoAtual):
        """
        Organizamos a chamada de cada método, realizando a sequência geral do AG:
        Ranquear a população, selecionar os que vão se reproduzir, gerar o grupo
        de reprodução, aplicar o crossover e aplicar a mutação, retornando a nova
        população.
        """
        popRanqueada = self.ranquearIndividuos(geracaoAtual)
        print(
            f"Best: {popRanqueada[0][0]}: {popRanqueada[0][1]}"
        )  # -> {geracaoAtual[popRanqueada[0][0]][1].pesos}")
        resSelecao = self.selecao(popRanqueada, self.tamElite)
        grReproducao = self.grupoDeReproducao(geracaoAtual, resSelecao)
        filhos = self.acasalaPppulacao(grReproducao, self.tamElite)
        proximaGeracao = self.mutacaoPopulacao(filhos, self.taxaMutacao)
        return proximaGeracao

    def AGT(self):
        """
        Chamada principal do treinamento por AG. Iniciamos uma população, e repetimos
        o número de gerações determinado no construtor para que os indivíduos evoluam.
        Ao final, retornamos o melhor individuo da última geração e o progresso da
        aptidão, para fins de visualização.
        """
        print("Iniciando treino AG...")
        pop = self.iniciaPopulacao(self.nIndividuos)
        progresso = []
        progresso.append(self.ranquearIndividuos(pop, self.treino)[0][1])
        print("Aptidão inicial: " + str(progresso[0]))
        print("Iniciando evolução")
        bar = tqdm(range(self.geracoes))
        for i in bar:
            bar.set_description(f"Geração {i+1}")
            bar.set_postfix(Aptidão=progresso[i])
            pop = self.proximaGeracao(self.treino, pop, self.elite, self.taxaMutacao)
            # import ipdb; ipdb.set_trace()
            progresso.append(self.ranquearIndividuos(pop, self.treino)[0][1])
        print()
        print("Aptidão final: " + str(progresso[-1]))
        indiceMelhorRota = self.ranquearIndividuos(pop, self.treino)[0][0]
        melhor = pop[indiceMelhorRota]
        return (melhor, progresso)
