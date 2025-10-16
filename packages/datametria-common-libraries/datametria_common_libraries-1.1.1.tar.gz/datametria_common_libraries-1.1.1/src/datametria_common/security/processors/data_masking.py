"""
Data Masking Processor - Mascaramento Automático de Dados Sensíveis

Processador structlog para compliance LGPD/GDPR com mascaramento de:
- CPF, CNPJ, RG
- Email, telefone
- Cartão de crédito
- Campos sensíveis (password, token, secret)

Autor: DATAMETRIA Team
Versão: 2.0.0
Compliance: LGPD Art. 46, GDPR Art. 32
"""

import re
from typing import Any, Dict, List, Pattern, Set, Tuple


class DataMaskingProcessor:
    """Processador structlog para mascaramento automático de dados sensíveis.
    
    Mascara automaticamente:
    - Padrões conhecidos: CPF, CNPJ, email, telefone, cartão de crédito
    - Campos sensíveis: password, token, secret, key
    - Padrões customizados via regex
    
    Preserva formato para análise mantendo domínios de email e estrutura.
    
    Attributes:
        SENSITIVE_PATTERNS (Dict): Padrões regex para dados sensíveis
        SENSITIVE_FIELDS (Set): Campos que devem ser mascarados
        custom_patterns (List): Padrões customizados adicionais
        
    Example:
        >>> processor = DataMaskingProcessor()
        >>> event_dict = {"email": "user@example.com", "password": "secret123"}
        >>> masked = processor(None, None, event_dict)
        >>> print(masked["email"])  # "***@example.com"
        >>> print(masked["password"])  # "se***23"
    """
    
    # Padrões sensíveis brasileiros e internacionais
    SENSITIVE_PATTERNS: Dict[str, Tuple[str, str]] = {
        'cpf': (r'\d{3}\.\d{3}\.\d{3}-\d{2}', '***.***.***-**'),
        'cpf_raw': (r'\b\d{11}\b', '***********'),
        'cnpj': (r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '**.***.***/****-**'),
        'cnpj_raw': (r'\b\d{14}\b', '**************'),
        'rg': (r'\d{2}\.\d{3}\.\d{3}-\d{1}', '**.***.***-*'),
        'email': (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'***@\2'),
        'phone_br': (r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}', '(**) ****-****'),
        'phone_intl': (r'\+\d{1,3}\s?\d{1,4}\s?\d{1,4}\s?\d{1,9}', '+** *** *** ****'),
        'credit_card': (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '**** **** **** ****'),
        'ip_address': (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '***.***.***.***'),
    }
    
    # Campos que devem ser mascarados (case-insensitive)
    SENSITIVE_FIELDS: Set[str] = {
        'password', 'senha', 'pass', 'pwd',
        'token', 'access_token', 'refresh_token', 'auth_token',
        'secret', 'api_secret', 'client_secret',
        'key', 'api_key', 'private_key', 'secret_key',
        'authorization', 'auth',
        'credential', 'credentials',
        'ssn', 'social_security',
        'credit_card', 'card_number', 'cvv', 'cvc',
    }
    
    def __init__(self, custom_patterns: List[Tuple[str, str]] = None, preserve_length: bool = False):
        """Inicializa data masking processor.
        
        Args:
            custom_patterns (List[Tuple[str, str]]): Padrões customizados (regex, replacement)
            preserve_length (bool): Se True, preserva tamanho original do valor
        """
        self.custom_patterns = custom_patterns or []
        self.preserve_length = preserve_length
    
    def __call__(self, logger, method_name, event_dict):
        """Processa e mascara dados sensíveis no event dict.
        
        Args:
            logger: Logger instance (não usado)
            method_name: Nome do método (não usado)
            event_dict (Dict): Dicionário de evento a processar
            
        Returns:
            Dict: Event dict com dados mascarados
        """
        # Processar cada campo do event dict
        for key, value in list(event_dict.items()):
            if self._is_sensitive_field(key):
                event_dict[key] = self._mask_value(value)
            elif isinstance(value, str):
                event_dict[key] = self._mask_patterns(value)
            elif isinstance(value, dict):
                event_dict[key] = self._mask_dict(value)
            elif isinstance(value, (list, tuple)):
                event_dict[key] = self._mask_list(value)
        
        return event_dict
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Verifica se campo é sensível.
        
        Args:
            field_name (str): Nome do campo
            
        Returns:
            bool: True se campo é sensível
        """
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.SENSITIVE_FIELDS)
    
    def _mask_value(self, value: Any) -> str:
        """Mascara valor sensível preservando formato.
        
        Args:
            value (Any): Valor a mascarar
            
        Returns:
            str: Valor mascarado
        """
        if not isinstance(value, str):
            return "***"
        
        if len(value) == 0:
            return ""
        
        if len(value) <= 4:
            return "***"
        
        if self.preserve_length:
            return "*" * len(value)
        
        # Preservar primeiros 2 e últimos 2 caracteres
        return f"{value[:2]}***{value[-2:]}"
    
    def _mask_patterns(self, text: str) -> str:
        """Mascara padrões sensíveis no texto.
        
        Args:
            text (str): Texto a processar
            
        Returns:
            str: Texto com padrões mascarados
        """
        if not isinstance(text, str):
            return text
        
        masked_text = text
        
        # Aplicar padrões built-in
        for pattern_name, (pattern, replacement) in self.SENSITIVE_PATTERNS.items():
            masked_text = re.sub(pattern, replacement, masked_text)
        
        # Aplicar padrões customizados
        for pattern, replacement in self.custom_patterns:
            masked_text = re.sub(pattern, replacement, masked_text)
        
        return masked_text
    
    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mascara dados sensíveis em dicionário recursivamente.
        
        Args:
            data (Dict): Dicionário a processar
            
        Returns:
            Dict: Dicionário com dados mascarados
        """
        masked = {}
        
        for key, value in data.items():
            if self._is_sensitive_field(key):
                masked[key] = self._mask_value(value)
            elif isinstance(value, str):
                masked[key] = self._mask_patterns(value)
            elif isinstance(value, dict):
                masked[key] = self._mask_dict(value)
            elif isinstance(value, (list, tuple)):
                masked[key] = self._mask_list(value)
            else:
                masked[key] = value
        
        return masked
    
    def _mask_list(self, data: List[Any]) -> List[Any]:
        """Mascara dados sensíveis em lista.
        
        Args:
            data (List): Lista a processar
            
        Returns:
            List: Lista com dados mascarados
        """
        masked = []
        
        for item in data:
            if isinstance(item, str):
                masked.append(self._mask_patterns(item))
            elif isinstance(item, dict):
                masked.append(self._mask_dict(item))
            elif isinstance(item, (list, tuple)):
                masked.append(self._mask_list(item))
            else:
                masked.append(item)
        
        return masked
    
    def add_custom_pattern(self, pattern: str, replacement: str) -> None:
        """Adiciona padrão customizado de mascaramento.
        
        Args:
            pattern (str): Regex pattern
            replacement (str): String de substituição
            
        Example:
            >>> processor.add_custom_pattern(r'\\bPROJ-\\d{4}\\b', 'PROJ-****')
        """
        self.custom_patterns.append((pattern, replacement))
    
    def add_sensitive_field(self, field_name: str) -> None:
        """Adiciona campo sensível à lista.
        
        Args:
            field_name (str): Nome do campo
            
        Example:
            >>> processor.add_sensitive_field('internal_id')
        """
        self.SENSITIVE_FIELDS.add(field_name.lower())
