# 💼 Carteira de Investimentos

Sistema web para controle de carteira de investimentos, inspirado no KINVO.
Projeto de estudo desenvolvido durante meu curso de Python.

🌐 **Ao vivo:** [fredhansen.pythonanywhere.com](https://fredhansen.pythonanywhere.com)

## 🎯 Funcionalidades

- ✅ Cadastro, edição e exclusão de ativos (ações, FIIs, renda fixa, ETFs)
- ✅ Registro de transações de compra e venda
- ✅ Cotações via yfinance, com cache para carregamento rápido
- ✅ Posição por ativo (quantidade, preço médio, custo) calculada a partir das transações
- ✅ Rentabilidade e comparação histórica com o IBOV (base 100)
- ✅ Gráficos interativos com Plotly (alocação da carteira e evolução vs. benchmark)
- ✅ Interface responsiva com Bootstrap e mensagens de feedback ao usuário
- 🚧 Análise de risco e indicadores técnicos *(próximos passos)*

## 🛠️ Tecnologias

- **Python 3.14** — linguagem principal
- **Flask** — framework web
- **SQLAlchemy + SQLite** — banco de dados
- **yfinance** — cotações do mercado
- **Pandas** — manipulação de dados
- **Plotly** — gráficos interativos
- **Bootstrap 5** — interface

## 🚀 Como executar

1. Clone o repositório:
   ```
   git clone https://github.com/fredhansenads/SantusPYF.git
   cd SantusPYF
   ```
2. Crie e ative o ambiente virtual (Windows):
   ```
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Rode a aplicação:
   ```
   python app.py
   ```
5. Acesse `http://127.0.0.1:5000` no navegador.

O banco de dados SQLite é criado automaticamente na primeira execução (pasta `instance/`).

## 📚 Aprendizados

Este projeto faz parte da minha jornada de aprendizagem em Python.
Cada etapa foi construída passo a passo: rotas Flask, modelagem de dados
com ORM, templates Jinja2, formulários HTML, integração com API de cotações,
cálculos financeiros com pandas, cache, tratamento de erros e versionamento com Git.

## 👤 Autor

Fred Hansen — [GitHub](https://github.com/fredhansenads)
