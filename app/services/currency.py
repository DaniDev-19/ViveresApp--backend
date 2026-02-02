import httpx
from datetime import datetime
from app.models.rate import ExchangeRate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CurrencyService:
    async def fetch_bcv(self) -> float:
        """Obtiene la tasa BCV desde DolarApi.com"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://ve.dolarapi.com/v1/dolares/oficial",
                    timeout=10.0
                )
                data = response.json()
                # El BCV oficial usa 4+ decimales
                return round(float(data.get("promedio", 0)), 4)
        except Exception as e:
            print(f"Error fetching BCV: {e}")
            return 0.0

    async def fetch_usdt(self) -> float:
        """Obtiene la tasa USDT (Binance P2P)"""
        # Intentamos usar Monitor Dolar como fuente más precisa de USDT/Paralelo
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://ve.dolarapi.com/v1/dolares/paralelo",
                    timeout=10.0
                )
                data = response.json()
                return round(float(data.get("promedio", 0)), 2)
        except Exception as e:
            print(f"Error fetching USDT: {e}")
            return 0.0

    async def fetch_cop(self) -> float:
        """Obtiene la tasa COP -> USD"""
        try:
            # API gratuita de ExchangeRate
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.exchangerate-api.com/v4/latest/USD"
                )
                data = response.json()
                return float(data["rates"]["COP"])
        except Exception:
            return 4000.0  # Valor por defecto seguro en caso de fallo

    async def update_rates(self, db: AsyncSession):
        """Actualiza todas las tasas en la Base de Datos"""
        bcv = await self.fetch_bcv()
        usdt = await self.fetch_usdt()
        cop = await self.fetch_cop()

        rates = [
            ExchangeRate(currency="BCV", rate=bcv, fetched_at=datetime.now()),
            ExchangeRate(currency="USDT", rate=usdt, fetched_at=datetime.now()),
            ExchangeRate(currency="COP", rate=cop, fetched_at=datetime.now()),
        ]

        db.add_all(rates)
        await db.commit()
        return {"BCV": bcv, "USDT": usdt, "COP": cop}

    async def get_latest_rates(self, db: AsyncSession):
        """Obtiene las últimas tasas desde la BD"""
        stmt = select(ExchangeRate).order_by(ExchangeRate.fetched_at.desc()).limit(3)
        result = await db.execute(stmt)
        rates = result.scalars().all()

        # Si no hay tasas, intentamos actualizarlas ahora mismo
        if not rates:
            await self.update_rates(db)
            result = await db.execute(stmt)
            rates = result.scalars().all()

        return rates


currency_service = CurrencyService()
