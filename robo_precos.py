"""Robô que coleta preços de uma loja online, guarda o histórico e avisa quando um preço muda."""

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_INICIAL = "https://books.toscrape.com/catalogue/page-1.html"
ESTRELAS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
CABECALHOS = {"User-Agent": "robo-de-precos/1.0 (projeto de estudo)"}


@dataclass
class Produto:
    nome: str
    preco: float
    em_estoque: bool
    avaliacao: int
    url: str


def converter_preco(texto: str) -> float:
    """Aceita '£51.77', 'R$ 1.234,56' ou '19.90'."""
    limpo = "".join(c for c in texto if c.isdigit() or c in ",.")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    return float(limpo)


def extrair_produtos(html: str, url_pagina: str) -> tuple[list[Produto], str | None]:
    """Lê uma página de listagem e devolve os produtos e o link da próxima página."""
    sopa = BeautifulSoup(html, "html.parser")
    produtos = []
    for card in sopa.select("article.product_pod"):
        link = card.select_one("h3 a")
        estrelas = card.select_one("p.star-rating")["class"]
        produtos.append(
            Produto(
                nome=link["title"],
                preco=converter_preco(card.select_one("p.price_color").get_text()),
                em_estoque="In stock" in card.select_one("p.availability").get_text(),
                avaliacao=next((ESTRELAS[c] for c in estrelas if c in ESTRELAS), 0),
                url=urljoin(url_pagina, link["href"]),
            )
        )
    proxima = sopa.select_one("li.next a")
    return produtos, urljoin(url_pagina, proxima["href"]) if proxima else None


def coletar(url: str = URL_INICIAL, paginas: int = 1, pausa: float = 1.0) -> list[Produto]:
    produtos = []
    sessao = requests.Session()
    sessao.headers.update(CABECALHOS)
    for n in range(paginas):
        resposta = sessao.get(url, timeout=20)
        resposta.raise_for_status()
        resposta.encoding = "utf-8"
        novos, url = extrair_produtos(resposta.text, url)
        produtos.extend(novos)
        print(f"Página {n + 1}: {len(novos)} produtos")
        if not url:
            break
        time.sleep(pausa)  # não sobrecarregar o site
    return produtos


def comparar(anterior: pd.DataFrame, atual: pd.DataFrame) -> pd.DataFrame:
    """Lista os produtos cujo preço mudou desde a coleta anterior."""
    juntos = atual.merge(anterior[["url", "preco"]], on="url", suffixes=("", "_anterior"))
    mudou = juntos[juntos["preco"] != juntos["preco_anterior"]].copy()
    mudou["variacao_%"] = ((mudou["preco"] / mudou["preco_anterior"] - 1) * 100).round(1)
    return mudou[["nome", "preco_anterior", "preco", "variacao_%", "url"]]


def verificar_alvos(atual: pd.DataFrame, alvos: dict[str, float]) -> pd.DataFrame:
    """Produtos que estão abaixo do preço desejado. `alvos` mapeia trecho do nome para preço máximo."""
    achados = []
    for trecho, preco_max in alvos.items():
        filtro = atual["nome"].str.contains(trecho, case=False, regex=False) & (atual["preco"] <= preco_max)
        for _, linha in atual[filtro].iterrows():
            achados.append({"busca": trecho, "preco_alvo": preco_max, **linha.to_dict()})
    return pd.DataFrame(achados)


def ultima_coleta(historico: pd.DataFrame) -> pd.DataFrame | None:
    if historico.empty:
        return None
    return historico[historico["data_coleta"] == historico["data_coleta"].max()]


def executar(produtos: list[Produto], pasta: Path, alvos: dict[str, float]) -> dict:
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo_historico = pasta / "historico.csv"
    historico = pd.read_csv(arquivo_historico) if arquivo_historico.exists() else pd.DataFrame()

    atual = pd.DataFrame([asdict(p) for p in produtos])
    atual["data_coleta"] = datetime.now().isoformat(timespec="seconds")

    anterior = ultima_coleta(historico)
    mudancas = comparar(anterior, atual) if anterior is not None else pd.DataFrame()
    encontrados = verificar_alvos(atual, alvos)

    pd.concat([historico, atual], ignore_index=True).to_csv(arquivo_historico, index=False)
    with pd.ExcelWriter(pasta / "relatorio_precos.xlsx") as planilha:
        atual.sort_values("preco").to_excel(planilha, sheet_name="Preços", index=False)
        mudancas.to_excel(planilha, sheet_name="Mudanças", index=False)
        encontrados.to_excel(planilha, sheet_name="Alertas", index=False)

    return {"produtos": len(atual), "mudancas": mudancas, "alertas": encontrados}


def main():
    parser = argparse.ArgumentParser(description="Coleta preços e avisa sobre mudanças.")
    parser.add_argument("--url", default=URL_INICIAL)
    parser.add_argument("--paginas", type=int, default=1)
    parser.add_argument("--alvos", type=Path, help="JSON com {\"trecho do nome\": preço máximo}")
    parser.add_argument("--pasta", type=Path, default=Path("saida"))
    args = parser.parse_args()

    alvos = json.loads(args.alvos.read_text(encoding="utf-8")) if args.alvos else {}
    resultado = executar(coletar(args.url, args.paginas), args.pasta, alvos)

    print(f"\n{resultado['produtos']} produtos salvos em {args.pasta / 'relatorio_precos.xlsx'}")
    for _, m in resultado["mudancas"].iterrows():
        print(f"  Preço mudou: {m['nome']}: {m['preco_anterior']} -> {m['preco']} ({m['variacao_%']}%)")
    for _, a in resultado["alertas"].iterrows():
        print(f"  ALERTA: {a['nome']} está por {a['preco']} (alvo: {a['preco_alvo']})")


if __name__ == "__main__":
    main()