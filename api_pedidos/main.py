from enum import Enum
from fastapi import FastAPI
from typing import Optional

app = FastAPI()


class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


pedidos = [
    {
        "id": 1,
        "cliente": "Ana López",
        "producto": "Laptop",
        "cantidad": 1,
        "total": 18500,
        "ciudad": "Toluca",
        "estado": "entregado"
    },
    {
        "id": 2,
        "cliente": "Carlos Pérez",
        "producto": "Teclado mecánico",
        "cantidad": 2,
        "total": 2400,
        "ciudad": "Metepec",
        "estado": "enviado"
    },
    {
        "id": 3,
        "cliente": "Mariana Torres",
        "producto": "Monitor",
        "cantidad": 1,
        "total": 5200,
        "ciudad": "Toluca",
        "estado": "pendiente"
    },
    {
        "id": 4,
        "cliente": "Luis Hernández",
        "producto": "Mouse inalámbrico",
        "cantidad": 3,
        "total": 1800,
        "ciudad": "Lerma",
        "estado": "entregado"
    },
    {
        "id": 5,
        "cliente": "Sofía Ramírez",
        "producto": "Audífonos",
        "cantidad": 1,
        "total": 1500,
        "ciudad": "Metepec",
        "estado": "cancelado"
    },
    {
        "id": 6,
        "cliente": "Diego Sánchez",
        "producto": "Tablet",
        "cantidad": 2,
        "total": 7600,
        "ciudad": "Toluca",
        "estado": "enviado"
    },
    {
        "id": 7,
        "cliente": "Valeria Gómez",
        "producto": "Webcam",
        "cantidad": 1,
        "total": 2100,
        "ciudad": "Zinacantepec",
        "estado": "pendiente"
    },
    {
        "id": 8,
        "cliente": "Jorge Martínez",
        "producto": "Impresora",
        "cantidad": 1,
        "total": 4300,
        "ciudad": "Lerma",
        "estado": "entregado"
    },
    {
        "id": 9,
        "cliente": "Fernanda Ruiz",
        "producto": "SSD 1TB",
        "cantidad": 2,
        "total": 3200,
        "ciudad": "Toluca",
        "estado": "cancelado"
    },
    {
        "id": 10,
        "cliente": "Ricardo Flores",
        "producto": "Silla gamer",
        "cantidad": 1,
        "total": 6800,
        "ciudad": "Metepec",
        "estado": "enviado"
    }
]


@app.get("/pedidos")
def obtener_pedidos(
        estado: Optional[EstadoPedido] = None,
        ciudad: Optional[str] = None
):
    resultados = pedidos

    if estado is not None:
        resultados = [
            pedido for pedido in resultados
            if pedido["estado"] == estado.value
        ]

    if ciudad is not None:
        resultados = [
            pedido for pedido in resultados
            if pedido["ciudad"].lower() == ciudad.lower()
        ]

    return resultados
