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


def _pasta_do_treino(semente):
    """treinos/<AAAAMMDD-HHMMSS>_s<semente>, com sufixo -2, -3... se o nome já existe."""
    base = os.path.join("treinos", time.strftime("%Y%m%d-%H%M%S") + f"_s{semente}")
    caminho, n = base, 2
    while os.path.exists(caminho):
        caminho, n = f"{base}-{n}", n + 1
    return caminho


def _rede_mais_recente(raiz="treinos"):
    """bestDino.din da pasta de treino mais recente em `raiz` (os nomes começam pela data), ou None."""
    if not os.path.isdir(raiz):
        return None
    for nome in sorted(os.listdir(raiz), reverse=True):
        caminho = os.path.join(raiz, nome, "bestDino.din")
        if os.path.isfile(caminho):
            return caminho
    return None


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
    saida = args.saida or _pasta_do_treino(semente)
    if os.path.exists(os.path.join(saida, "fitness.csv")):  # nunca sobrescrever um treino
        print(f"Pasta já tem um treino: {saida}")
        return 1
    game = DinoGame.DinoGame()
    if args.sem_janela:
        os.makedirs(saida, exist_ok=True)
        game.train(args.individuos, args.geracoes, semente, saida, janela=False)
    elif not game.introscreen():  # introscreen devolve True se o usuário fechou
        os.makedirs(saida, exist_ok=True)
        game.train(args.individuos, args.geracoes, semente, saida)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exception(e)
        if len(sys.argv) == 1:  # aberto com duplo clique: não fecha o terminal na hora
            input("Press enter to close the terminal window")
        sys.exit(1)
