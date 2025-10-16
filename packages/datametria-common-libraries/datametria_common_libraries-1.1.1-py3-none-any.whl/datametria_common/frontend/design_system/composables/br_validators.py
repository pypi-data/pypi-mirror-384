"""
Brazilian Validators Composables DATAMETRIA

Composables reutilizáveis para validações e formatações brasileiras.
"""

import re
from typing import Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Resultado de validação"""
    is_valid: bool
    error_message: str = ""


class BRValidators:
    """Validadores brasileiros"""
    
    @staticmethod
    def validate_cep(cep: str) -> ValidationResult:
        """Valida CEP brasileiro"""
        clean = re.sub(r'\D', '', cep)
        
        if not clean:
            return ValidationResult(False, "")
        
        if len(clean) != 8:
            return ValidationResult(False, "CEP deve ter 8 dígitos")
        
        if re.match(r'^(0{8}|1{8}|2{8}|3{8}|4{8}|5{8}|6{8}|7{8}|8{8}|9{8})$', clean):
            return ValidationResult(False, "CEP inválido")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> ValidationResult:
        """Valida CNPJ brasileiro"""
        clean = re.sub(r'\D', '', cnpj)
        
        if not clean:
            return ValidationResult(False, "")
        
        if len(clean) != 14:
            return ValidationResult(False, "CNPJ deve ter 14 dígitos")
        
        if re.match(r'^(\d)\1{13}$', clean):
            return ValidationResult(False, "CNPJ inválido")
        
        digits = [int(d) for d in clean]
        
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(digits[i] * weights1[i] for i in range(12))
        digit1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)
        
        if digits[12] != digit1:
            return ValidationResult(False, "CNPJ inválido")
        
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(digits[i] * weights2[i] for i in range(13))
        digit2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)
        
        if digits[13] != digit2:
            return ValidationResult(False, "CNPJ inválido")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_cpf(cpf: str) -> ValidationResult:
        """Valida CPF brasileiro"""
        clean = re.sub(r'\D', '', cpf)
        
        if not clean:
            return ValidationResult(False, "")
        
        if len(clean) != 11:
            return ValidationResult(False, "CPF deve ter 11 dígitos")
        
        if re.match(r'^(\d)\1{10}$', clean):
            return ValidationResult(False, "CPF inválido")
        
        digits = [int(d) for d in clean]
        
        sum1 = sum(digits[i] * (10 - i) for i in range(9))
        digit1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)
        
        if digits[9] != digit1:
            return ValidationResult(False, "CPF inválido")
        
        sum2 = sum(digits[i] * (11 - i) for i in range(10))
        digit2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)
        
        if digits[10] != digit2:
            return ValidationResult(False, "CPF inválido")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_phone(phone: str, phone_type: str = "any") -> ValidationResult:
        """Valida telefone brasileiro"""
        clean = re.sub(r'\D', '', phone)
        
        if not clean:
            return ValidationResult(False, "")
        
        if phone_type == "mobile" and len(clean) != 11:
            return ValidationResult(False, "Celular deve ter 11 dígitos")
        
        if phone_type == "landline" and len(clean) != 10:
            return ValidationResult(False, "Telefone fixo deve ter 10 dígitos")
        
        if phone_type == "any" and len(clean) not in [10, 11]:
            return ValidationResult(False, "Telefone deve ter 10 ou 11 dígitos")
        
        if re.match(r'^(\d)\1+$', clean):
            return ValidationResult(False, "Telefone inválido")
        
        area_code = int(clean[:2])
        if area_code < 11 or area_code > 99:
            return ValidationResult(False, "Código de área inválido")
        
        if len(clean) == 11 and clean[2] != '9':
            return ValidationResult(False, "Celular deve começar com 9")
        
        if len(clean) == 10 and clean[2] in ['0', '1', '9']:
            return ValidationResult(False, "Primeiro dígito do fixo inválido")
        
        return ValidationResult(True)


class BRFormatters:
    """Formatadores brasileiros"""
    
    @staticmethod
    def format_cep(value: str) -> str:
        """Formata CEP: 00000-000"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 5:
            return clean
        return f"{clean[:5]}-{clean[5:8]}"
    
    @staticmethod
    def format_cnpj(value: str) -> str:
        """Formata CNPJ: 00.000.000/0000-00"""
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
    
    @staticmethod
    def format_cpf(value: str) -> str:
        """Formata CPF: 000.000.000-00"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 3:
            return clean
        if len(clean) <= 6:
            return f"{clean[:3]}.{clean[3:]}"
        if len(clean) <= 9:
            return f"{clean[:3]}.{clean[3:6]}.{clean[6:]}"
        return f"{clean[:3]}.{clean[3:6]}.{clean[6:9]}-{clean[9:11]}"
    
    @staticmethod
    def format_phone(value: str) -> str:
        """Formata telefone: (00) 00000-0000 ou (00) 0000-0000"""
        clean = re.sub(r'\D', '', value)
        if len(clean) <= 2:
            return clean
        if len(clean) <= 6:
            return f"({clean[:2]}) {clean[2:]}"
        if len(clean) <= 10:
            return f"({clean[:2]}) {clean[2:6]}-{clean[6:]}"
        return f"({clean[:2]}) {clean[2:7]}-{clean[7:11]}"


__all__ = ["BRValidators", "BRFormatters", "ValidationResult"]
