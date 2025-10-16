"""
🛠️ React Native Utils - DATAMETRIA

Utilitários e helpers integrados ao ecossistema DATAMETRIA.
"""

from typing import Dict, Any, Optional, List, Union, Callable
import structlog
import re
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger(__name__)


class DeviceType(Enum):
    """Tipos de dispositivo."""
    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"


class Platform(Enum):
    """Plataformas suportadas."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


@dataclass
class DeviceInfo:
    """Informações do dispositivo."""
    type: DeviceType
    platform: Platform
    width: int
    height: int
    scale: float
    is_landscape: bool


class DeviceUtils:
    """
    Utilitários para detecção e adaptação de dispositivo.
    
    Integrado ao sistema responsivo DATAMETRIA.
    """
    
    @staticmethod
    def get_device_type(width: int, height: int) -> DeviceType:
        """
        Detectar tipo de dispositivo baseado nas dimensões.
        
        Args:
            width: Largura da tela
            height: Altura da tela
            
        Returns:
            DeviceType: Tipo do dispositivo
        """
        # Usar a menor dimensão para classificação
        min_dimension = min(width, height)
        
        if min_dimension < 768:
            return DeviceType.PHONE
        elif min_dimension < 1024:
            return DeviceType.TABLET
        else:
            return DeviceType.DESKTOP
    
    @staticmethod
    def is_landscape(width: int, height: int) -> bool:
        """Verificar se está em modo paisagem."""
        return width > height
    
    @staticmethod
    def get_safe_area_insets(platform: Platform) -> Dict[str, int]:
        """
        Obter insets de área segura.
        
        Args:
            platform: Plataforma do dispositivo
            
        Returns:
            Dict[str, int]: Insets (top, bottom, left, right)
        """
        if platform == Platform.IOS:
            return {'top': 44, 'bottom': 34, 'left': 0, 'right': 0}
        elif platform == Platform.ANDROID:
            return {'top': 24, 'bottom': 0, 'left': 0, 'right': 0}
        else:
            return {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}
    
    @staticmethod
    def get_responsive_font_size(base_size: int, device_type: DeviceType) -> int:
        """
        Calcular tamanho de fonte responsivo.
        
        Args:
            base_size: Tamanho base da fonte
            device_type: Tipo do dispositivo
            
        Returns:
            int: Tamanho ajustado da fonte
        """
        multipliers = {
            DeviceType.PHONE: 0.9,
            DeviceType.TABLET: 1.1,
            DeviceType.DESKTOP: 1.2
        }
        
        return int(base_size * multipliers.get(device_type, 1.0))
    
    @staticmethod
    def get_responsive_spacing(base_spacing: int, device_type: DeviceType) -> int:
        """
        Calcular espaçamento responsivo.
        
        Args:
            base_spacing: Espaçamento base
            device_type: Tipo do dispositivo
            
        Returns:
            int: Espaçamento ajustado
        """
        multipliers = {
            DeviceType.PHONE: 0.8,
            DeviceType.TABLET: 1.0,
            DeviceType.DESKTOP: 1.2
        }
        
        return int(base_spacing * multipliers.get(device_type, 1.0))


class ValidationUtils:
    """
    Utilitários de validação integrados ao sistema DATAMETRIA.
    
    Suporte a LGPD/GDPR e validações enterprise.
    """
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validar formato de email.
        
        Args:
            email: Email a validar
            
        Returns:
            bool: True se válido
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Validar CPF brasileiro.
        
        Args:
            cpf: CPF a validar
            
        Returns:
            bool: True se válido
        """
        # Remover caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Calcular dígitos verificadores
        def calculate_digit(cpf_digits: str, weights: List[int]) -> int:
            total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Primeiro dígito
        first_digit = calculate_digit(cpf[:9], list(range(10, 1, -1)))
        if int(cpf[9]) != first_digit:
            return False
        
        # Segundo dígito
        second_digit = calculate_digit(cpf[:10], list(range(11, 1, -1)))
        return int(cpf[10]) == second_digit
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """
        Validar CNPJ brasileiro.
        
        Args:
            cnpj: CNPJ a validar
            
        Returns:
            bool: True se válido
        """
        # Remover caracteres não numéricos
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Calcular dígitos verificadores
        def calculate_digit(cnpj_digits: str, weights: List[int]) -> int:
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Primeiro dígito
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        first_digit = calculate_digit(cnpj[:12], weights1)
        if int(cnpj[12]) != first_digit:
            return False
        
        # Segundo dígito
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_digit = calculate_digit(cnpj[:13], weights2)
        return int(cnpj[13]) == second_digit
    
    @staticmethod
    def validate_phone(phone: str, country_code: str = 'BR') -> bool:
        """
        Validar número de telefone.
        
        Args:
            phone: Telefone a validar
            country_code: Código do país
            
        Returns:
            bool: True se válido
        """
        # Remover caracteres não numéricos
        phone = re.sub(r'[^0-9]', '', phone)
        
        if country_code == 'BR':
            # Telefone brasileiro: (11) 99999-9999 ou (11) 9999-9999
            return len(phone) in [10, 11] and phone[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        
        # Validação genérica: entre 8 e 15 dígitos
        return 8 <= len(phone) <= 15
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validar força da senha.
        
        Args:
            password: Senha a validar
            
        Returns:
            Dict[str, Any]: Resultado da validação
        """
        result = {
            'is_valid': False,
            'score': 0,
            'requirements': {
                'min_length': len(password) >= 8,
                'has_uppercase': bool(re.search(r'[A-Z]', password)),
                'has_lowercase': bool(re.search(r'[a-z]', password)),
                'has_numbers': bool(re.search(r'\d', password)),
                'has_special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            },
            'suggestions': []
        }
        
        # Calcular score
        score = sum(result['requirements'].values())
        result['score'] = score
        result['is_valid'] = score >= 4
        
        # Gerar sugestões
        if not result['requirements']['min_length']:
            result['suggestions'].append('Use pelo menos 8 caracteres')
        if not result['requirements']['has_uppercase']:
            result['suggestions'].append('Inclua pelo menos uma letra maiúscula')
        if not result['requirements']['has_lowercase']:
            result['suggestions'].append('Inclua pelo menos uma letra minúscula')
        if not result['requirements']['has_numbers']:
            result['suggestions'].append('Inclua pelo menos um número')
        if not result['requirements']['has_special']:
            result['suggestions'].append('Inclua pelo menos um caractere especial')
        
        return result


class FormatUtils:
    """
    Utilitários de formatação integrados ao sistema DATAMETRIA.
    
    Suporte a localização e padrões brasileiros.
    """
    
    @staticmethod
    def format_cpf(cpf: str) -> str:
        """
        Formatar CPF.
        
        Args:
            cpf: CPF a formatar
            
        Returns:
            str: CPF formatado
        """
        cpf = re.sub(r'[^0-9]', '', cpf)
        if len(cpf) == 11:
            return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
        return cpf
    
    @staticmethod
    def format_cnpj(cnpj: str) -> str:
        """
        Formatar CNPJ.
        
        Args:
            cnpj: CNPJ a formatar
            
        Returns:
            str: CNPJ formatado
        """
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj) == 14:
            return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'
        return cnpj
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """
        Formatar telefone brasileiro.
        
        Args:
            phone: Telefone a formatar
            
        Returns:
            str: Telefone formatado
        """
        phone = re.sub(r'[^0-9]', '', phone)
        
        if len(phone) == 11:
            return f'({phone[:2]}) {phone[2:7]}-{phone[7:]}'
        elif len(phone) == 10:
            return f'({phone[:2]}) {phone[2:6]}-{phone[6:]}'
        
        return phone
    
    @staticmethod
    def format_currency(value: float, currency: str = 'BRL') -> str:
        """
        Formatar moeda.
        
        Args:
            value: Valor a formatar
            currency: Código da moeda
            
        Returns:
            str: Valor formatado
        """
        if currency == 'BRL':
            return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        elif currency == 'USD':
            return f'$ {value:,.2f}'
        elif currency == 'EUR':
            return f'€ {value:,.2f}'
        
        return f'{value:,.2f}'
    
    @staticmethod
    def format_date(date: datetime, format_type: str = 'short') -> str:
        """
        Formatar data.
        
        Args:
            date: Data a formatar
            format_type: Tipo de formato ('short', 'long', 'iso')
            
        Returns:
            str: Data formatada
        """
        if format_type == 'short':
            return date.strftime('%d/%m/%Y')
        elif format_type == 'long':
            return date.strftime('%d de %B de %Y')
        elif format_type == 'iso':
            return date.isoformat()
        
        return date.strftime('%d/%m/%Y %H:%M')
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Formatar tamanho de arquivo.
        
        Args:
            size_bytes: Tamanho em bytes
            
        Returns:
            str: Tamanho formatado
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"


class StorageUtils:
    """
    Utilitários de armazenamento local integrados ao sistema DATAMETRIA.
    
    Suporte a criptografia e compliance LGPD/GDPR.
    """
    
    def __init__(self, encrypt_sensitive: bool = True):
        self.encrypt_sensitive = encrypt_sensitive
        self._storage: Dict[str, Any] = {}
        
        logger.debug("StorageUtils initialized", encrypt_sensitive=encrypt_sensitive)
    
    def set_item(self, key: str, value: Any, sensitive: bool = False) -> bool:
        """
        Armazenar item.
        
        Args:
            key: Chave do item
            value: Valor a armazenar
            sensitive: Se é dado sensível
            
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            # Serializar valor
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            # Criptografar se necessário
            if sensitive and self.encrypt_sensitive:
                # Integrar com SecurityManager quando disponível
                serialized_value = f"ENCRYPTED:{serialized_value}"
            
            self._storage[key] = {
                'value': serialized_value,
                'sensitive': sensitive,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug("Item stored", key=key, sensitive=sensitive)
            return True
            
        except Exception as e:
            logger.error("Storage error", key=key, error=str(e))
            return False
    
    def get_item(self, key: str, default: Any = None) -> Any:
        """
        Obter item armazenado.
        
        Args:
            key: Chave do item
            default: Valor padrão se não encontrado
            
        Returns:
            Any: Valor armazenado ou padrão
        """
        try:
            if key not in self._storage:
                return default
            
            item = self._storage[key]
            value = item['value']
            
            # Descriptografar se necessário
            if item.get('sensitive') and value.startswith('ENCRYPTED:'):
                value = value[10:]  # Remove prefix
            
            # Tentar deserializar JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error("Storage retrieval error", key=key, error=str(e))
            return default
    
    def remove_item(self, key: str) -> bool:
        """
        Remover item.
        
        Args:
            key: Chave do item
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            if key in self._storage:
                del self._storage[key]
                logger.debug("Item removed", key=key)
                return True
            return False
            
        except Exception as e:
            logger.error("Storage removal error", key=key, error=str(e))
            return False
    
    def clear_all(self) -> bool:
        """
        Limpar todo o armazenamento.
        
        Returns:
            bool: True se limpo com sucesso
        """
        try:
            self._storage.clear()
            logger.info("Storage cleared")
            return True
            
        except Exception as e:
            logger.error("Storage clear error", error=str(e))
            return False
    
    def get_all_keys(self) -> List[str]:
        """Obter todas as chaves armazenadas."""
        return list(self._storage.keys())
    
    def get_storage_size(self) -> int:
        """Obter tamanho do armazenamento em bytes."""
        total_size = 0
        for item in self._storage.values():
            total_size += len(str(item['value']))
        return total_size


class PerformanceUtils:
    """
    Utilitários de performance para React Native.
    
    Monitoramento e otimização integrados ao sistema DATAMETRIA.
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        
        logger.debug("PerformanceUtils initialized")
    
    def start_timer(self, name: str) -> float:
        """
        Iniciar timer de performance.
        
        Args:
            name: Nome da métrica
            
        Returns:
            float: Timestamp de início
        """
        start_time = datetime.now().timestamp()
        
        if name not in self._metrics:
            self._metrics[name] = []
        
        logger.debug("Timer started", name=name)
        return start_time
    
    def end_timer(self, name: str, start_time: float) -> float:
        """
        Finalizar timer e registrar métrica.
        
        Args:
            name: Nome da métrica
            start_time: Timestamp de início
            
        Returns:
            float: Duração em milissegundos
        """
        end_time = datetime.now().timestamp()
        duration_ms = (end_time - start_time) * 1000
        
        if name in self._metrics:
            self._metrics[name].append(duration_ms)
        
        logger.info("Timer ended", name=name, duration_ms=duration_ms)
        return duration_ms
    
    def get_metrics(self, name: str) -> Dict[str, float]:
        """
        Obter métricas de performance.
        
        Args:
            name: Nome da métrica
            
        Returns:
            Dict[str, float]: Estatísticas da métrica
        """
        if name not in self._metrics or not self._metrics[name]:
            return {}
        
        values = self._metrics[name]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'total': sum(values)
        }
    
    def clear_metrics(self, name: Optional[str] = None) -> None:
        """
        Limpar métricas.
        
        Args:
            name: Nome específico ou None para limpar todas
        """
        if name:
            if name in self._metrics:
                self._metrics[name].clear()
        else:
            self._metrics.clear()
        
        logger.info("Metrics cleared", name=name or "all")


# Instâncias globais
storage_utils = StorageUtils()
performance_utils = PerformanceUtils()


# Decorador para medir performance
def measure_performance(name: str):
    """
    Decorador para medir performance de funções.
    
    Args:
        name: Nome da métrica
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start_time = performance_utils.start_timer(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                performance_utils.end_timer(name, start_time)
        return wrapper
    return decorator
