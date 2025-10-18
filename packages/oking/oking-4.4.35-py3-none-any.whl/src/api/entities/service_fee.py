from dataclasses import dataclass

@dataclass
class ServiceFee:
    percentual_taxa_servico: float
    codigo_escopo: str
    tipo_escopo: str
