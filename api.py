from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()

engine = create_engine("sqlite:///gastos.db")
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    telefone = Column(String, index=True)
    categoria = Column(String)
    valor = Column(Float)

Base.metadata.create_all(bind=engine)

def categoria_padrao(nome):
    nome = nome.lower()

    if nome in ["gasolina", "uber", "onibus", "ônibus", "metro", "metrô"]:
        return "transporte"
    elif nome in ["lanche", "ifood", "mercado", "restaurante", "compra", "mochila"]:
        return "alimentacao"
    else:
        return nome

def extrair_gasto(texto):
    partes = texto.lower().split()

    valor = None
    palavras_categoria = []
    ignorar = ["gastei", "com", "no", "na", "de", "reais", "real", "r$"]

    for p in partes:
        numero = p.replace(",", ".")
        try:
            valor = float(numero)
        except:
            if p not in ignorar:
                palavras_categoria.append(p)

    categoria = categoria_padrao(" ".join(palavras_categoria))
    return categoria, valor

@app.get("/")
def inicio():
    return {"mensagem": "Bot financeiro multiusuario 🚀"}

@app.post("/whatsapp", response_class=PlainTextResponse)
def receber_whatsapp(Body: str = Form(...), From: str = Form(...)):
    db = SessionLocal()
    texto = Body.strip().lower()
    telefone = From.strip()

    if texto == "menu":
        return (
            "👋 *Bem-vinda ao seu bot financeiro!*\n\n"
            "📌 Comandos:\n"
            "• Enviar gasto: *gasolina 150*\n"
            "• *total*\n"
            "• *resumo*\n"
            "• *gastos*\n"
            "• *meunumero*\n\n"
            "🗑️ Para apagar: *apagar 1*"
        )

    if texto == "meunumero":
        return f"📱 Seu identificador no sistema é:\n*{telefone}*"

    if texto == "total":
        gastos = db.query(Gasto).filter(Gasto.telefone == telefone).all()
        total = sum(g.valor for g in gastos)

        return (
            "📊 *Seu total de gastos*\n\n"
            f"💸 Total: *R$ {total:.2f}*".replace(".", ",")
        )

    if texto == "resumo":
        gastos = db.query(Gasto).filter(Gasto.telefone == telefone).all()

        resumo = {}
        for g in gastos:
            resumo[g.categoria] = resumo.get(g.categoria, 0) + g.valor

        if not resumo:
            return "📭 *Você ainda não tem gastos salvos.*"

        linhas = ["📌 *Resumo dos seus gastos:*\n"]
        for categoria, valor in resumo.items():
            linhas.append(f"• *{categoria}*: R$ {valor:.2f}".replace(".", ","))

        return "\n".join(linhas)

    if texto == "gastos":
        gastos = (
            db.query(Gasto)
            .filter(Gasto.telefone == telefone)
            .order_by(Gasto.id.desc())
            .limit(10)
            .all()
        )

        gastos = list(reversed(gastos))

        if not gastos:
            return "📭 *Você ainda não tem gastos salvos.*"

        linhas = ["🧾 *Seus gastos:*\n"]
        for i, g in enumerate(gastos, start=1):
            linhas.append(f"{i}. {g.categoria} — R$ {g.valor:.2f}".replace(".", ","))

        linhas.append("\n🗑️ Para apagar, digite: *apagar 1*")
        return "\n".join(linhas)

    if texto.startswith("apagar"):
        partes = texto.split()

        if len(partes) != 2 or not partes[1].isdigit():
            return "❌ Use assim: *apagar 1*"

        indice = int(partes[1]) - 1

        gastos = (
            db.query(Gasto)
            .filter(Gasto.telefone == telefone)
            .order_by(Gasto.id.desc())
            .limit(10)
            .all()
        )

        gastos = list(reversed(gastos))

        if indice < 0 or indice >= len(gastos):
            return "❌ Número inválido."

        db.delete(gastos[indice])
        db.commit()

        return "🗑️ *Gasto removido com sucesso!*"

    categoria, valor = extrair_gasto(texto)

    if not categoria or valor is None:
        return (
            "⚠️ *Não entendi sua mensagem.*\n\n"
            "Envie assim:\n"
            "*gasolina 150*\n"
            "*uber 10,99*\n\n"
            "Ou digite *menu*."
        )

    novo_gasto = Gasto(
        telefone=telefone,
        categoria=categoria,
        valor=valor
    )
    db.add(novo_gasto)
    db.commit()

    return (
        "✅ *Gasto registrado com sucesso!*\n\n"
        f"📂 Categoria: *{categoria}*\n"
        f"💰 Valor: *R$ {valor:.2f}*".replace(".", ",")
    )