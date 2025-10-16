"""
🛠️ DATAMETRIA Common Utilities

Utilitários comuns e funções auxiliares para a biblioteca DATAMETRIA Common Libraries.
Fornece funcionalidades essenciais para configuração, validação e manipulação de dados.

Features:
    - Gerenciamento de variáveis de ambiente com validação
    - Utilitários de validação de dados
    - Funções de formatação e conversão
    - Helpers para logging e debugging
    - Utilitários gerais de sistema

Note:
    Para funções de segurança (mascaramento, criptografia), use:
    - datametria_common.security.security_manager.SecurityManager
    - datametria_common.database.connectors.oracle.security.OracleSecurityManager

Examples:
    >>> from datametria_common.utils import get_env_var, validate_email
    >>> db_host = get_env_var("DB_HOST", "localhost")
    >>> is_valid = validate_email("user@example.com")

Author: Equipe DATAMETRIA
Version: 1.0.0
Date: 2025-01-08
License: MIT
"""

import os
import re
import logging
from typing import Any, Optional, Union, Dict, List
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


def get_env_var(
    name: str, 
    default: Optional[str] = None, 
    required: bool = False,
    cast_type: type = str
) -> Any:
    """Obtém variável de ambiente com validação e conversão de tipo.
    
    Args:
        name (str): Nome da variável de ambiente
        default (Optional[str]): Valor padrão se variável não existir
        required (bool): Se True, levanta exceção se variável não existir
        cast_type (type): Tipo para conversão do valor
        
    Returns:
        Any: Valor da variável de ambiente convertido para o tipo especificado
        
    Raises:
        ValueError: Se variável obrigatória não existir ou conversão falhar
        
    Examples:
        >>> db_host = get_env_var("DB_HOST", "localhost")
        >>> db_port = get_env_var("DB_PORT", "5432", cast_type=int)
        >>> debug_mode = get_env_var("DEBUG", "false", cast_type=bool)
    """
    try:
        value = os.getenv(name, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable '{name}' not found")
            
        if value is None:
            return None
            
        # Convert boolean strings
        if cast_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
            
        # Convert to specified type
        return cast_type(value)
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error processing environment variable '{name}': {e}")
        if required:
            raise
        return default


def validate_email(email: str) -> bool:
    """Valida formato de email.
    
    Args:
        email (str): Email para validação
        
    Returns:
        bool: True se email válido, False caso contrário
        
    Example:
        >>> is_valid = validate_email("user@example.com")
        >>> print(is_valid)  # True
    """
    if not email or not isinstance(email, str):
        return False
        
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """Sanitiza nome de arquivo removendo caracteres inválidos.
    
    Args:
        filename (str): Nome do arquivo para sanitizar
        
    Returns:
        str: Nome do arquivo sanitizado
        
    Example:
        >>> clean_name = sanitize_filename("file<>name.txt")
        >>> print(clean_name)  # "filename.txt"
    """
    if not filename:
        return "unnamed_file"
        
    # Remove caracteres inválidos
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '', filename)
    
    # Remove espaços extras
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    
    return sanitized or "unnamed_file"





def safe_dict_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Obtém valor de dicionário de forma segura.
    
    Args:
        dictionary (Dict[str, Any]): Dicionário fonte
        key (str): Chave para buscar
        default (Any): Valor padrão se chave não existir
        
    Returns:
        Any: Valor encontrado ou padrão
        
    Example:
        >>> config = {"host": "localhost"}
        >>> host = safe_dict_get(config, "host", "127.0.0.1")
    """
    try:
        return dictionary.get(key, default) if isinstance(dictionary, dict) else default
    except (AttributeError, TypeError):
        return default


def ensure_directory(path: Union[str, Path]) -> Path:
    """Garante que diretório existe, criando se necessário.
    
    Args:
        path (Union[str, Path]): Caminho do diretório
        
    Returns:
        Path: Objeto Path do diretório
        
    Raises:
        OSError: Se não conseguir criar o diretório
        
    Example:
        >>> log_dir = ensure_directory("logs")
        >>> print(log_dir.exists())  # True
    """
    path_obj = Path(path)
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    except OSError as e:
        logger.error(f"Failed to create directory '{path}': {e}")
        raise


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em formato legível.
    
    Args:
        size_bytes (int): Tamanho em bytes
        
    Returns:
        str: Tamanho formatado (ex: "1.5 MB")
        
    Example:
        >>> size = format_file_size(1536000)
        >>> print(size)  # "1.5 MB"
    """
    if size_bytes == 0:
        return "0 B"
        
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.1f} {units[unit_index]}"


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Faz merge profundo de dois dicionários.
    
    Args:
        dict1 (Dict[str, Any]): Dicionário base
        dict2 (Dict[str, Any]): Dicionário para merge
        
    Returns:
        Dict[str, Any]: Dicionário resultante do merge
        
    Example:
        >>> base = {"db": {"host": "localhost"}}
        >>> override = {"db": {"port": 5432}}
        >>> result = deep_merge_dicts(base, override)
        >>> print(result)  # {"db": {"host": "localhost", "port": 5432}}
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
            
    return result
