# Robô de monitoramento de preços

Coleta os preços de uma loja online, guarda o histórico a cada execução e avisa quando um preço muda ou quando um produto fica abaixo do valor que você quer pagar. O resultado sai numa planilha Excel com três abas: preços atuais, mudanças e alertas.

**Problema que resolve:** lojistas e compradores precisam acompanhar preços da concorrência ou de fornecedores, e fazer isso na mão todo dia toma tempo.

O exemplo usa o [Books to Scrape](https://books.toscrape.com), um site feito para treinar coleta de dados. Para outra loja, troque os seletores na função `extrair_produtos`.

## Como usar

Requer Python 3.10 ou mais novo.

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

python robo_precos.py --paginas 3
python robo_precos.py --paginas 3 --alvos alvos.json
```

Exemplo de saída no terminal. As linhas de mudança e alerta só aparecem a partir da segunda execução, quando algum preço mudou ou bateu o alvo:

```
Página 1: 20 produtos
Página 2: 20 produtos
Página 3: 20 produtos

60 produtos salvos em saida/relatorio_precos.xlsx
  Preço mudou: Soumission: 50.1 -> 40.0 (-20.2%)
  ALERTA: Soumission está por 40.0 (alvo: 45.0)
```

O arquivo `alvos.json` define os produtos que você quer vigiar e o preço máximo:

```json
{ "soumission": 45.0 }
```

Para rodar todo dia sozinho, agende com o `cron` (Linux/Mac) ou o Agendador de Tarefas (Windows).

## Como funciona

1. Baixa cada página de listagem e segue o link "próxima", com uma pausa entre as páginas para não sobrecarregar o site.
2. Extrai nome, preço, estoque, avaliação e link de cada produto.
3. Compara com a última coleta salva em `saida/historico.csv`.
4. Gera `saida/relatorio_precos.xlsx`.

## Estrutura

| Arquivo | O que faz |
|---|---|
| `robo_precos.py` | Coleta, extração, comparação com a coleta anterior, alertas e planilha |
| `alvos.json` | Produtos a vigiar e o preço máximo de cada um |
| `tests/fixtures/pagina.html` | Página salva, usada nos testes |
| `tests/` | Testes com pytest |

## Testes

Os testes usam uma página HTML salva, então rodam sem internet:

```bash
pytest
```

## Tecnologias

Python, requests, BeautifulSoup, pandas.

## Ideias de evolução

- Guardar o histórico em SQLite em vez de CSV.
- Enviar os alertas por e-mail, Telegram ou WhatsApp.
- Gerar um gráfico da variação de preço de cada produto ao longo do tempo.

## Uso responsável

Antes de coletar dados de um site, leia os termos de uso e o `robots.txt`, e mantenha um intervalo entre as requisições.

## Autor

Feito por **Luis Lopo**, desenvolvedor Python, Java e TypeScript. Faço automações, relatórios e chatbots sob medida para pequenos negócios. Veja os outros projetos no meu perfil do GitHub.