"""
Theme Sync Manager

Sistema de sincronização de temas entre dispositivos usando Vault Manager.
"""

from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from .manager import ThemeMode
from ...utilities.vault_manager import VaultManager


@dataclass
class SyncConfig:
    """Configuração de sincronização"""
    enabled: bool = True
    vault_path: str = "datametria/themes"
    sync_interval: int = 300  # 5 minutos
    auto_sync: bool = True


class ThemeSyncManager:
    """
    Gerenciador de sincronização de temas usando Vault Manager existente
    
    Aproveita o VaultManager já implementado para sincronizar preferências
    de tema entre dispositivos do usuário.
    """
    
    def __init__(self, config: SyncConfig, vault_manager: Optional[VaultManager] = None):
        self.config = config
        self.vault_manager = vault_manager
        self._sync_callbacks: list[Callable[[ThemeMode], None]] = []
        self._last_sync_timestamp = 0.0
        
        if self.config.enabled and not self.vault_manager:
            # Usar VaultManager existente se disponível
            try:
                self.vault_manager = VaultManager()
            except Exception:
                self.config.enabled = False
    
    def sync_theme_to_cloud(self, user_id: str, theme_mode: ThemeMode) -> bool:
        """
        Sincroniza tema para a nuvem
        
        Args:
            user_id: ID do usuário
            theme_mode: Modo de tema a sincronizar
            
        Returns:
            True se sincronização foi bem-sucedida
        """
        if not self.config.enabled or not self.vault_manager:
            return False
        
        try:
            theme_data = {
                "mode": theme_mode.value,
                "timestamp": self._get_timestamp(),
                "device_id": self._get_device_id(),
                "version": "1.0.0"
            }
            
            vault_path = f"{self.config.vault_path}/{user_id}/theme"
            
            # Usar VaultManager para salvar
            success = self.vault_manager.store_secret(vault_path, theme_data)
            
            if success:
                self._last_sync_timestamp = theme_data["timestamp"]
            
            return success
            
        except Exception as e:
            print(f"Error syncing theme to cloud: {e}")
            return False
    
    def sync_theme_from_cloud(self, user_id: str) -> Optional[ThemeMode]:
        """
        Sincroniza tema da nuvem
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Modo de tema sincronizado ou None se não encontrado
        """
        if not self.config.enabled or not self.vault_manager:
            return None
        
        try:
            vault_path = f"{self.config.vault_path}/{user_id}/theme"
            
            # Usar VaultManager para recuperar
            theme_data = self.vault_manager.get_secret(vault_path)
            
            if not theme_data or not isinstance(theme_data, dict):
                return None
            
            # Verificar se é mais recente que o último sync
            cloud_timestamp = theme_data.get("timestamp", 0)
            if cloud_timestamp <= self._last_sync_timestamp:
                return None
            
            mode_value = theme_data.get("mode")
            if mode_value:
                self._last_sync_timestamp = cloud_timestamp
                return ThemeMode(mode_value)
                
        except Exception as e:
            print(f"Error syncing theme from cloud: {e}")
        
        return None
    
    def add_sync_callback(self, callback: Callable[[ThemeMode], None]) -> None:
        """
        Adiciona callback para quando tema é sincronizado da nuvem
        
        Args:
            callback: Função a ser chamada com o novo tema
        """
        self._sync_callbacks.append(callback)
    
    def remove_sync_callback(self, callback: Callable[[ThemeMode], None]) -> None:
        """
        Remove callback de sincronização
        
        Args:
            callback: Função a ser removida
        """
        if callback in self._sync_callbacks:
            self._sync_callbacks.remove(callback)
    
    def start_auto_sync(self, user_id: str) -> None:
        """
        Inicia sincronização automática
        
        Args:
            user_id: ID do usuário para sincronizar
        """
        if not self.config.auto_sync or not self.config.enabled:
            return
        
        # Implementação real usaria threading ou asyncio
        # Para demonstração, apenas verifica uma vez
        self._check_cloud_updates(user_id)
    
    def stop_auto_sync(self) -> None:
        """Para sincronização automática"""
        # Implementação real pararia threads/tasks
        pass
    
    def _check_cloud_updates(self, user_id: str) -> None:
        """Verifica atualizações na nuvem"""
        try:
            synced_theme = self.sync_theme_from_cloud(user_id)
            if synced_theme:
                # Notificar callbacks
                for callback in self._sync_callbacks:
                    try:
                        callback(synced_theme)
                    except Exception as e:
                        print(f"Error in sync callback: {e}")
        except Exception as e:
            print(f"Error checking cloud updates: {e}")
    
    def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna status da sincronização
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com status da sincronização
        """
        return {
            "enabled": self.config.enabled,
            "vault_available": self.vault_manager is not None,
            "last_sync": self._last_sync_timestamp,
            "auto_sync": self.config.auto_sync,
            "sync_interval": self.config.sync_interval,
            "callbacks_count": len(self._sync_callbacks)
        }
    
    def force_sync(self, user_id: str, theme_mode: ThemeMode) -> Dict[str, bool]:
        """
        Força sincronização bidirecional
        
        Args:
            user_id: ID do usuário
            theme_mode: Tema atual local
            
        Returns:
            Status das operações de sync
        """
        results = {
            "upload": False,
            "download": False,
            "conflict_resolved": False
        }
        
        if not self.config.enabled:
            return results
        
        try:
            # Tentar baixar tema da nuvem primeiro
            cloud_theme = self.sync_theme_from_cloud(user_id)
            
            if cloud_theme and cloud_theme != theme_mode:
                # Há conflito - usar timestamp para resolver
                results["conflict_resolved"] = True
                results["download"] = True
            else:
                # Fazer upload do tema local
                results["upload"] = self.sync_theme_to_cloud(user_id, theme_mode)
                
        except Exception as e:
            print(f"Error in force sync: {e}")
        
        return results
    
    def _get_timestamp(self) -> float:
        """Retorna timestamp atual"""
        import time
        return time.time()
    
    def _get_device_id(self) -> str:
        """Retorna ID único do dispositivo"""
        import platform
        import hashlib
        
        # Gerar ID baseado em informações do sistema
        system_info = f"{platform.node()}-{platform.system()}-{platform.machine()}"
        return hashlib.md5(system_info.encode()).hexdigest()[:16]


class CloudThemeSync:
    """
    Wrapper simplificado para sincronização de temas
    
    Integra DarkModeManager com ThemeSyncManager
    """
    
    def __init__(self, user_id: str, vault_manager: Optional[VaultManager] = None):
        self.user_id = user_id
        self.sync_config = SyncConfig()
        self.sync_manager = ThemeSyncManager(self.sync_config, vault_manager)
    
    def enable_sync(self) -> bool:
        """Habilita sincronização"""
        self.sync_config.enabled = True
        return self.sync_manager.vault_manager is not None
    
    def disable_sync(self) -> None:
        """Desabilita sincronização"""
        self.sync_config.enabled = False
        self.sync_manager.stop_auto_sync()
    
    def sync_theme(self, theme_mode: ThemeMode) -> bool:
        """
        Sincroniza tema atual
        
        Args:
            theme_mode: Tema a ser sincronizado
            
        Returns:
            True se sincronização foi bem-sucedida
        """
        return self.sync_manager.sync_theme_to_cloud(self.user_id, theme_mode)
    
    def get_synced_theme(self) -> Optional[ThemeMode]:
        """
        Obtém tema sincronizado da nuvem
        
        Returns:
            Tema sincronizado ou None
        """
        return self.sync_manager.sync_theme_from_cloud(self.user_id)
    
    def is_sync_available(self) -> bool:
        """Verifica se sincronização está disponível"""
        return (self.sync_config.enabled and 
                self.sync_manager.vault_manager is not None)


# Export
__all__ = [
    "SyncConfig",
    "ThemeSyncManager",
    "CloudThemeSync",
]
