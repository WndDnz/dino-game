#!/usr/bin/python3
"""Treina os dinos com janela (padrão) ou sem janela, ou mostra uma rede salva jogando."""

import argparse
import os
import sys
import time
import traceback


def _um_ou_mais(texto):
    n = int(texto)
    if n < 1:
        raise argparse.ArgumentTypeError("deve ser 1 ou mais")
    return n


def _semente(texto):
    n = int(texto)
    if not 0 <= n <= 2**32 - 1:  # faixa aceita por np.random.seed
        raise argparse.ArgumentTypeError("deve estar entre 0 e 4294967295")
    return n


def _cria_pasta(base):
    """Cria `base`, ou base-2, base-3... a primeira que não existe, e devolve o caminho.
    Criar a pasta é a reserva: dois treinos simultâneos nunca recebem a mesma."""
    caminho, n = base, 2
    while True:
        try:
            os.makedirs(caminho)
            return caminho
        except FileExistsError:
            caminho, n = f"{base}-{n}", n + 1


def _pasta_do_treino(semente):
    """Cria treinos/<AAAAMMDD-HHMMSS>_s<semente> (ou com sufixo -2, -3...) e devolve o caminho."""
    return _cria_pasta(os.path.join("treinos", time.strftime("%Y%m%d-%H%M%S") + f"_s{semente}"))


def _rede_mais_recente(raiz="treinos"):
    """O bestDino.din gravado por último entre as pastas de `raiz`, ou None."""
    if not os.path.isdir(raiz):
        return None
    redes = [os.path.join(raiz, nome, "bestDino.din") for nome in os.listdir(raiz)]
    redes = [r for r in redes if os.path.isfile(r)]
    return max(redes, key=os.path.getmtime, default=None)


def main(argv=None):
    """Interpreta as opções, roda o modo pedido e devolve o código de saída."""
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--sem-janela", action="store_true", help="treina sem abrir janela"
    )
    modo.add_argument(
        "--assistir",
        nargs="?",
        const="",
        metavar="ARQUIVO",
        help="mostra a rede salva jogando (padrão: a do treino mais recente em treinos/)",
    )
    parser.add_argument("--individuos", type=_um_ou_mais, default=350)
    parser.add_argument("--geracoes", type=_um_ou_mais, default=30)
    parser.add_argument(
        "--pistas",
        type=_um_ou_mais,
        default=5,
        help="pistas de treino por geração; o fitness é a média nelas (padrão 5)",
    )
    parser.add_argument(
        "--saida",
        metavar="PASTA",
        help="pasta do treino (padrão: treinos/<data-hora>_s<semente>)",
    )
    parser.add_argument(
        "--semente",
        type=_semente,
        help="treino: semente base (padrão 0); assistir: mesma pista em toda partida",
    )
    args = parser.parse_args(argv)  # opção inválida: mensagem de uso e código 2

    if args.sem_janela:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    # só agora: o pygame escolhe o driver de vídeo quando é iniciado, na importação
    import DinoGame

    if args.assistir is not None:
        if args.assistir == "":
            args.assistir = _rede_mais_recente()
            if args.assistir is None:
                print("Nenhum treino encontrado em: treinos")
                return 1
        try:
            rede = DinoGame.carrega_rede(args.assistir)
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {args.assistir}")
            return 1
        except ValueError:
            print(f"Arquivo inválido: {args.assistir}")
            return 1
        DinoGame.DinoGame().gameplay(rede=rede, semente=args.semente)
        return 0

    semente = args.semente or 0

    def tem_treino(pasta):
        return os.path.exists(os.path.join(pasta, "fitness.csv"))

    if args.saida and tem_treino(args.saida):  # nunca sobrescrever um treino
        print(f"Pasta já tem um treino: {args.saida}")
        return 1

    def pasta():
        """A pasta do próximo treino, criada agora, logo antes de treinar."""
        if not args.saida:
            return _pasta_do_treino(semente)
        if not tem_treino(args.saida):
            os.makedirs(args.saida, exist_ok=True)
            return args.saida
        return _cria_pasta(os.path.normpath(args.saida))  # novo treino pedido na tela de fim

    game = DinoGame.DinoGame()
    if args.sem_janela:
        game.train(args.individuos, args.geracoes, semente, pasta(), janela=False, pistas=args.pistas)
    elif not game.introscreen():  # introscreen devolve True se o usuário fechou
        # train devolve True quando o usuário pede outro treino na tela de fim
        while game.train(args.individuos, args.geracoes, semente, pasta(), pistas=args.pistas):
            pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exception(e)
        if len(sys.argv) == 1:  # aberto com duplo clique: não fecha o terminal na hora
            input("Press enter to close the terminal window")
        sys.exit(1)
