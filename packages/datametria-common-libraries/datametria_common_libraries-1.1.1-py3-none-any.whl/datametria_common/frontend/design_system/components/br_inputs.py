"""
Brazilian Input Components DATAMETRIA

Inputs especializados para validações brasileiras: CEP, CNPJ, CPF, Phone.
"""

from dataclasses import dataclass
from typing import Optional, Callable
import re


@dataclass
class DatametriaCEPInput:
    """Input de CEP com validação e integração ViaCEP"""
    value: str = ""
    label: str = "CEP"
    placeholder: str = "00000-000"
    required: bool = False
    disabled: bool = False
    
    def format(self, value: str) -> str:
        """Formata CEP"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 5:
            return clean
        return f"{clean[:5]}-{clean[5:8]}"
    
    def validate(self) -> tuple[bool, str]:
        """Valida CEP"""
        clean = re.sub(r'\D', '', self.value)
        
        if not clean:
            return (False, "CEP é obrigatório" if self.required else "")
        
        if len(clean) != 8:
            return (False, "CEP deve ter 8 dígitos")
        
        if re.match(r'^(0{8}|1{8}|2{8}|3{8}|4{8}|5{8}|6{8}|7{8}|8{8}|9{8})$', clean):
            return (False, "CEP inválido")
        
        return (True, "")
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
.dm-cep-input { position: relative; }
.dm-cep-input input { padding-left: 2.5rem; }
.dm-cep-input .icon { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #6b7280; }
.dm-cep-input .validation-icon { position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); }
.dm-cep-input .validation-icon.success { color: #22c55e; }
.dm-cep-input .validation-icon.error { color: #ef4444; }
"""


@dataclass
class DatametriaCNPJInput:
    """Input de CNPJ com validação completa"""
    value: str = ""
    label: str = "CNPJ"
    placeholder: str = "00.000.000/0000-00"
    required: bool = False
    disabled: bool = False
    
    def format(self, value: str) -> str:
        """Formata CNPJ"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 2:
            return clean
        if len(clean) <= 5:
            return f"{clean[:2]}.{clean[2:]}"
        if len(clean) <= 8:
            return f"{clean[:2]}.{clean[2:5]}.{clean[5:]}"
        if len(clean) <= 12:
            return f"{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:]}"
        return f"{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:14]}"
    
    def validate(self) -> tuple[bool, str]:
        """Valida CNPJ com algoritmo completo"""
        clean = re.sub(r'\D', '', self.value)
        
        if not clean:
            return (False, "CNPJ é obrigatório" if self.required else "")
        
        if len(clean) != 14:
            return (False, "CNPJ deve ter 14 dígitos")
        
        if re.match(r'^(\d)\1{13}$', clean):
            return (False, "CNPJ inválido")
        
        # Validação dos dígitos verificadores
        digits = [int(d) for d in clean]
        
        # Primeiro dígito
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(digits[i] * weights1[i] for i in range(12))
        digit1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)
        
        if digits[12] != digit1:
            return (False, "CNPJ inválido")
        
        # Segundo dígito
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(digits[i] * weights2[i] for i in range(13))
        digit2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)
        
        if digits[13] != digit2:
            return (False, "CNPJ inválido")
        
        return (True, "")
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
.dm-cnpj-input { position: relative; }
.dm-cnpj-input input { padding-left: 2.5rem; }
.dm-cnpj-input .icon { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #6b7280; }
.dm-cnpj-input .validation-icon { position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); }
.dm-cnpj-input .validation-icon.success { color: #22c55e; }
.dm-cnpj-input .validation-icon.error { color: #ef4444; }
"""


@dataclass
class DatametriaPhoneInput:
    """Input de telefone brasileiro com validação"""
    value: str = ""
    label: str = "Telefone"
    placeholder: str = "(00) 00000-0000"
    phone_type: str = "any"  # mobile, landline, any
    required: bool = False
    disabled: bool = False
    
    def format(self, value: str) -> str:
        """Formata telefone"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 2:
            return clean
        if len(clean) <= 6:
            return f"({clean[:2]}) {clean[2:]}"
        if len(clean) <= 10:
            return f"({clean[:2]}) {clean[2:6]}-{clean[6:]}"
        return f"({clean[:2]}) {clean[2:7]}-{clean[7:11]}"
    
    def validate(self) -> tuple[bool, str]:
        """Valida telefone brasileiro"""
        clean = re.sub(r'\D', '', self.value)
        
        if not clean:
            return (False, "Telefone é obrigatório" if self.required else "")
        
        if self.phone_type == "mobile" and len(clean) != 11:
            return (False, "Celular deve ter 11 dígitos")
        
        if self.phone_type == "landline" and len(clean) != 10:
            return (False, "Telefone fixo deve ter 10 dígitos")
        
        if self.phone_type == "any" and len(clean) not in [10, 11]:
            return (False, "Telefone deve ter 10 ou 11 dígitos")
        
        if re.match(r'^(\d)\1+$', clean):
            return (False, "Telefone inválido")
        
        area_code = int(clean[:2])
        if area_code < 11 or area_code > 99:
            return (False, "Código de área inválido")
        
        if len(clean) == 11 and clean[2] != '9':
            return (False, "Celular deve começar com 9")
        
        if len(clean) == 10 and clean[2] in ['0', '1', '9']:
            return (False, "Primeiro dígito do fixo inválido")
        
        return (True, "")
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
.dm-phone-input { position: relative; }
.dm-phone-input input { padding-left: 2.5rem; }
.dm-phone-input .icon { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #6b7280; }
.dm-phone-input .validation-icon { position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); }
.dm-phone-input .validation-icon.success { color: #22c55e; }
.dm-phone-input .validation-icon.error { color: #ef4444; }
"""


@dataclass
class DatametriaCPFInput:
    """Input de CPF com validação completa"""
    value: str = ""
    label: str = "CPF"
    placeholder: str = "000.000.000-00"
    required: bool = False
    disabled: bool = False
    
    def format(self, value: str) -> str:
        """Formata CPF"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 3:
            return clean
        if len(clean) <= 6:
            return f"{clean[:3]}.{clean[3:]}"
        if len(clean) <= 9:
            return f"{clean[:3]}.{clean[3:6]}.{clean[6:]}"
        return f"{clean[:3]}.{clean[3:6]}.{clean[6:9]}-{clean[9:11]}"
    
    def validate(self) -> tuple[bool, str]:
        """Valida CPF com algoritmo completo"""
        clean = re.sub(r'\D', '', self.value)
        
        if not clean:
            return (False, "CPF é obrigatório" if self.required else "")
        
        if len(clean) != 11:
            return (False, "CPF deve ter 11 dígitos")
        
        if re.match(r'^(\d)\1{10}$', clean):
            return (False, "CPF inválido")
        
        # Validação dos dígitos verificadores
        digits = [int(d) for d in clean]
        
        # Primeiro dígito
        sum1 = sum(digits[i] * (10 - i) for i in range(9))
        digit1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)
        
        if digits[9] != digit1:
            return (False, "CPF inválido")
        
        # Segundo dígito
        sum2 = sum(digits[i] * (11 - i) for i in range(10))
        digit2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)
        
        if digits[10] != digit2:
            return (False, "CPF inválido")
        
        return (True, "")
    
    def get_css(self) -> str:
        """Retorna CSS do componente"""
        return """
.dm-cpf-input { position: relative; }
.dm-cpf-input input { padding-left: 2.5rem; }
.dm-cpf-input .icon { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #6b7280; }
.dm-cpf-input .validation-icon { position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); }
.dm-cpf-input .validation-icon.success { color: #22c55e; }
.dm-cpf-input .validation-icon.error { color: #ef4444; }
"""


__all__ = [
    "DatametriaCEPInput",
    "DatametriaCNPJInput",
    "DatametriaPhoneInput",
    "DatametriaCPFInput",
]
