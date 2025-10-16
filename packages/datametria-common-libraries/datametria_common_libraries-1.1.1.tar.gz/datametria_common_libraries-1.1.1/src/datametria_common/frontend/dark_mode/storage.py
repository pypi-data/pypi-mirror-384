"""
Theme Storage System

Sistema de persistência de preferências de tema com suporte a múltiplos backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .manager import ThemeMode


class ThemeStorage(ABC):
    """Interface base para storage de temas"""
    
    @abstractmethod
    def save_theme(self, mode: ThemeMode) -> bool:
        """Salva modo de tema"""
        pass
    
    @abstractmethod
    def load_theme(self) -> Optional[ThemeMode]:
        """Carrega modo de tema salvo"""
        pass
    
    @abstractmethod
    def clear_theme(self) -> bool:
        """Remove tema salvo"""
        pass


class LocalThemeStorage(ThemeStorage):
    """Storage local usando localStorage (web) ou equivalente"""
    
    def __init__(self, key: str = "datametria-theme"):
        self.key = key
    
    def save_theme(self, mode: ThemeMode) -> bool:
        """Salva tema no localStorage"""
        try:
            # Simula localStorage (implementação real usaria localStorage do browser)
            import os
            os.environ[f"DATAMETRIA_STORAGE_{self.key}"] = mode.value
            return True
        except Exception:
            return False
    
    def load_theme(self) -> Optional[ThemeMode]:
        """Carrega tema do localStorage"""
        try:
            import os
            value = os.environ.get(f"DATAMETRIA_STORAGE_{self.key}")
            if value:
                return ThemeMode(value)
        except Exception:
            pass
        return None
    
    def clear_theme(self) -> bool:
        """Remove tema do localStorage"""
        try:
            import os
            key = f"DATAMETRIA_STORAGE_{self.key}"
            if key in os.environ:
                del os.environ[key]
            return True
        except Exception:
            return False


class SecureThemeStorage(ThemeStorage):
    """Storage seguro usando keychain/keystore do sistema"""
    
    def __init__(self, service: str = "datametria", account: str = "theme"):
        self.service = service
        self.account = account
    
    def save_theme(self, mode: ThemeMode) -> bool:
        """Salva tema no storage seguro"""
        try:
            # Implementação real usaria keyring ou similar
            # keyring.set_password(self.service, self.account, mode.value)
            
            # Simulação para desenvolvimento
            import os
            os.environ[f"SECURE_{self.service}_{self.account}"] = mode.value
            return True
        except Exception:
            return False
    
    def load_theme(self) -> Optional[ThemeMode]:
        """Carrega tema do storage seguro"""
        try:
            # Implementação real usaria keyring
            # value = keyring.get_password(self.service, self.account)
            
            # Simulação para desenvolvimento
            import os
            value = os.environ.get(f"SECURE_{self.service}_{self.account}")
            if value:
                return ThemeMode(value)
        except Exception:
            pass
        return None
    
    def clear_theme(self) -> bool:
        """Remove tema do storage seguro"""
        try:
            # Implementação real usaria keyring
            # keyring.delete_password(self.service, self.account)
            
            # Simulação para desenvolvimento
            import os
            key = f"SECURE_{self.service}_{self.account}"
            if key in os.environ:
                del os.environ[key]
            return True
        except Exception:
            return False


class DatabaseThemeStorage(ThemeStorage):
    """Storage em banco de dados para sincronização"""
    
    def __init__(self, user_id: str, db_connection=None):
        self.user_id = user_id
        self.db = db_connection
    
    def save_theme(self, mode: ThemeMode) -> bool:
        """Salva tema no banco de dados"""
        try:
            if not self.db:
                return False
            
            # Implementação real executaria SQL
            # self.db.execute(
            #     "INSERT OR REPLACE INTO user_preferences (user_id, theme_mode) VALUES (?, ?)",
            #     (self.user_id, mode.value)
            # )
            
            # Simulação para desenvolvimento
            import os
            os.environ[f"DB_THEME_{self.user_id}"] = mode.value
            return True
        except Exception:
            return False
    
    def load_theme(self) -> Optional[ThemeMode]:
        """Carrega tema do banco de dados"""
        try:
            if not self.db:
                return None
            
            # Implementação real executaria SQL
            # result = self.db.execute(
            #     "SELECT theme_mode FROM user_preferences WHERE user_id = ?",
            #     (self.user_id,)
            # ).fetchone()
            
            # Simulação para desenvolvimento
            import os
            value = os.environ.get(f"DB_THEME_{self.user_id}")
            if value:
                return ThemeMode(value)
        except Exception:
            pass
        return None
    
    def clear_theme(self) -> bool:
        """Remove tema do banco de dados"""
        try:
            if not self.db:
                return False
            
            # Implementação real executaria SQL
            # self.db.execute(
            #     "DELETE FROM user_preferences WHERE user_id = ?",
            #     (self.user_id,)
            # )
            
            # Simulação para desenvolvimento
            import os
            key = f"DB_THEME_{self.user_id}"
            if key in os.environ:
                del os.environ[key]
            return True
        except Exception:
            return False


class MultiLayerThemeStorage(ThemeStorage):
    """Storage com múltiplas camadas (local + seguro + cloud)"""
    
    def __init__(self, storages: list[ThemeStorage]):
        self.storages = storages
    
    def save_theme(self, mode: ThemeMode) -> bool:
        """Salva tema em todos os storages"""
        results = []
        for storage in self.storages:
            try:
                result = storage.save_theme(mode)
                results.append(result)
            except Exception:
                results.append(False)
        
        # Retorna True se pelo menos um storage funcionou
        return any(results)
    
    def load_theme(self) -> Optional[ThemeMode]:
        """Carrega tema do primeiro storage disponível"""
        for storage in self.storages:
            try:
                theme = storage.load_theme()
                if theme:
                    return theme
            except Exception:
                continue
        return None
    
    def clear_theme(self) -> bool:
        """Remove tema de todos os storages"""
        results = []
        for storage in self.storages:
            try:
                result = storage.clear_theme()
                results.append(result)
            except Exception:
                results.append(False)
        
        # Retorna True se todos os storages foram limpos
        return all(results)


class ThemeStorageFactory:
    """Factory para criar instâncias de storage"""
    
    @staticmethod
    def create_local_storage(key: str = "datametria-theme") -> LocalThemeStorage:
        """Cria storage local"""
        return LocalThemeStorage(key)
    
    @staticmethod
    def create_secure_storage(service: str = "datametria", account: str = "theme") -> SecureThemeStorage:
        """Cria storage seguro"""
        return SecureThemeStorage(service, account)
    
    @staticmethod
    def create_database_storage(user_id: str, db_connection=None) -> DatabaseThemeStorage:
        """Cria storage de banco de dados"""
        return DatabaseThemeStorage(user_id, db_connection)
    
    @staticmethod
    def create_multi_layer_storage(user_id: str = "default", db_connection=None) -> MultiLayerThemeStorage:
        """Cria storage multi-camada completo"""
        storages = [
            LocalThemeStorage(),
            SecureThemeStorage(),
        ]
        
        if user_id and db_connection:
            storages.append(DatabaseThemeStorage(user_id, db_connection))
        
        return MultiLayerThemeStorage(storages)


# Export
__all__ = [
    "ThemeStorage",
    "LocalThemeStorage",
    "SecureThemeStorage", 
    "DatabaseThemeStorage",
    "MultiLayerThemeStorage",
    "ThemeStorageFactory",
]
