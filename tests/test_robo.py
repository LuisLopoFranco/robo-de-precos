import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robo_precos import Produto, converter_preco, executar, extrair_produtos

FIXTURE = Path(__file__).parent / "fixtures" / "pagina.html"
URL = "https://books.toscrape.com/catalogue/page-1.html"


def test_converter_preco():
    assert converter_preco("£51.77") == 51.77
    assert converter_preco("R$ 1.234,56") == 1234.56
    assert converter_preco("19,90") == 19.90


def test_extrair_produtos():
    produtos, proxima = extrair_produtos(FIXTURE.read_text(encoding="utf-8"), URL)

    assert len(produtos) == 3
    primeiro = produtos[0]
    assert primeiro.nome == "A Light in the Attic"
    assert primeiro.preco == 51.77
    assert primeiro.em_estoque is True
    assert primeiro.avaliacao == 3
    assert primeiro.url == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert produtos[1].em_estoque is False
    assert proxima == "https://books.toscrape.com/catalogue/page-2.html"


def test_detecta_mudanca_de_preco_e_alerta(tmp_path):
    produtos, _ = extrair_produtos(FIXTURE.read_text(encoding="utf-8"), URL)
    executar(produtos, tmp_path, alvos={})

    # Segunda coleta: um livro ficou mais barato
    produtos[2] = Produto(**{**produtos[2].__dict__, "preco": 40.00})
    historico = pd.read_csv(tmp_path / "historico.csv")
    historico["data_coleta"] = "2000-01-01T00:00:00"  # garante que a primeira coleta fique como anterior
    historico.to_csv(tmp_path / "historico.csv", index=False)

    resultado = executar(produtos, tmp_path, alvos={"soumission": 45.0})

    mudancas = resultado["mudancas"]
    assert list(mudancas["nome"]) == ["Soumission"]
    assert mudancas.iloc[0]["variacao_%"] == -20.2
    assert list(resultado["alertas"]["nome"]) == ["Soumission"]
    assert len(pd.read_csv(tmp_path / "historico.csv")) == 6
    assert (tmp_path / "relatorio_precos.xlsx").exists()