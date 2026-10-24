# Chatbot de atendimento com IA para pequenos negócios

Atendente virtual para o site de um pequeno negócio (o exemplo é uma pizzaria). Ele responde sobre cardápio, horários, entrega e pagamento, e ajuda o cliente a montar o pedido com o valor total. Usa só as informações cadastradas em `negocio.json`, então não inventa preços nem promoções.

![Prévia do chat](docs/preview.png)

**Problema que resolve:** pequenos negócios perdem vendas porque demoram para responder perguntas repetidas. O bot atende na hora, 24 horas por dia.

## Como usar

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app:app --reload
```

Abra http://localhost:8000.

- **Sem chave de API:** roda em modo demonstração, respondendo por palavras-chave. Serve para mostrar a interface.
- **Com IA:** crie uma chave em https://platform.claude.com, defina `export ANTHROPIC_API_KEY=sua-chave` e reinicie o servidor. As respostas passam a ser geradas pelo Claude.

## Adaptar para outro cliente

Edite só o `negocio.json` (nome, endereço, horários, cardápio, regras). O comportamento do atendente está em `montar_instrucoes`, no arquivo `chatbot.py`.

## Estrutura

| Arquivo | O que faz |
|---|---|
| `chatbot.py` | Monta as instruções a partir do negócio, valida a conversa e chama a IA |
| `app.py` | API em FastAPI (`/api/chat`, `/api/status`) e serve a página |
| `static/index.html` | Interface do chat, sem framework |
| `negocio.json` | Dados do negócio |

## Testes

Os testes não chamam a API de verdade:

```bash
pytest
```

## Tecnologias

Python, FastAPI, API do Claude (Anthropic), HTML/CSS/JS.

## Ideias de evolução

- Ligar ao WhatsApp pela API oficial (Meta Cloud API).
- Salvar os pedidos num banco de dados e avisar a cozinha.
- Painel em Angular para o dono editar o cardápio.
