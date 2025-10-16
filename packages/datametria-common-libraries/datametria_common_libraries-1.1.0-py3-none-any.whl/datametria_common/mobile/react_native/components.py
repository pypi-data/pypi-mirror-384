"""
🧩 React Native Components - DATAMETRIA

Componentes React Native integrados ao Design System DATAMETRIA.
"""

from typing import Dict, Any, Optional, List, Callable, Union
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class ComponentProps:
    """Props base para componentes DATAMETRIA."""
    theme_aware: bool = True
    responsive: bool = True
    accessible: bool = True
    test_id: Optional[str] = None


@dataclass
class ResponsiveProps:
    """Props para responsividade."""
    phone: Optional[Dict[str, Any]] = None
    tablet: Optional[Dict[str, Any]] = None
    desktop: Optional[Dict[str, Any]] = None


class DatametriaScreen:
    """
    Componente Screen principal DATAMETRIA.
    
    Integra header, loading, error handling e refresh.
    """
    
    def __init__(
        self,
        header: Optional[Dict[str, Any]] = None,
        loading: bool = False,
        error: Optional[str] = None,
        on_refresh: Optional[Callable] = None,
        refreshing: bool = False,
        safe_area: bool = True,
        **props
    ):
        self.header = header
        self.loading = loading
        self.error = error
        self.on_refresh = on_refresh
        self.refreshing = refreshing
        self.safe_area = safe_area
        self.props = ComponentProps(**props)
        
        logger.debug("DatametriaScreen initialized", has_header=bool(header))
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaScreen',
            'props': {
                'header': self.header,
                'loading': self.loading,
                'error': self.error,
                'onRefresh': self.on_refresh,
                'refreshing': self.refreshing,
                'safeArea': self.safe_area,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            }
        }


class DatametriaButton:
    """
    Componente Button DATAMETRIA.
    
    Suporte a variantes, tamanhos responsivos e estados.
    """
    
    def __init__(
        self,
        title: str,
        on_press: Callable,
        variant: str = 'primary',
        size: str = 'md',
        loading: bool = False,
        disabled: bool = False,
        icon: Optional[str] = None,
        icon_position: str = 'left',
        responsive_size: Optional[ResponsiveProps] = None,
        **props
    ):
        self.title = title
        self.on_press = on_press
        self.variant = variant
        self.size = size
        self.loading = loading
        self.disabled = disabled
        self.icon = icon
        self.icon_position = icon_position
        self.responsive_size = responsive_size
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaButton initialized",
            variant=variant,
            size=size,
            has_icon=bool(icon)
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        config = {
            'component': 'DatametriaButton',
            'props': {
                'title': self.title,
                'onPress': self.on_press,
                'variant': self.variant,
                'size': self.size,
                'loading': self.loading,
                'disabled': self.disabled,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            }
        }
        
        if self.icon:
            config['props'].update({
                'icon': self.icon,
                'iconPosition': self.icon_position
            })
        
        if self.responsive_size:
            config['props']['responsiveSize'] = {
                'phone': self.responsive_size.phone,
                'tablet': self.responsive_size.tablet,
                'desktop': self.responsive_size.desktop
            }
        
        return config


class DatametriaInput:
    """
    Componente Input DATAMETRIA.
    
    Suporte a validação, máscaras e responsividade.
    """
    
    def __init__(
        self,
        label: str,
        value: str,
        on_change: Callable[[str], None],
        placeholder: Optional[str] = None,
        input_type: str = 'text',
        required: bool = False,
        error: Optional[str] = None,
        mask: Optional[str] = None,
        validation: Optional[Dict[str, Any]] = None,
        multiline: bool = False,
        secure: bool = False,
        **props
    ):
        self.label = label
        self.value = value
        self.on_change = on_change
        self.placeholder = placeholder
        self.input_type = input_type
        self.required = required
        self.error = error
        self.mask = mask
        self.validation = validation
        self.multiline = multiline
        self.secure = secure
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaInput initialized",
            label=label,
            input_type=input_type,
            required=required
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaInput',
            'props': {
                'label': self.label,
                'value': self.value,
                'onChangeText': self.on_change,
                'placeholder': self.placeholder,
                'inputType': self.input_type,
                'required': self.required,
                'error': self.error,
                'mask': self.mask,
                'validation': self.validation,
                'multiline': self.multiline,
                'secureTextEntry': self.secure,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            }
        }


class DatametriaCard:
    """
    Componente Card DATAMETRIA.
    
    Container com elevação e bordas responsivas.
    """
    
    def __init__(
        self,
        children: Optional[List[Any]] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        image: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        elevation: str = 'md',
        padding: str = 'md',
        **props
    ):
        self.children = children or []
        self.title = title
        self.subtitle = subtitle
        self.image = image
        self.actions = actions
        self.elevation = elevation
        self.padding = padding
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaCard initialized",
            has_title=bool(title),
            has_image=bool(image),
            actions_count=len(actions or [])
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaCard',
            'props': {
                'title': self.title,
                'subtitle': self.subtitle,
                'image': self.image,
                'actions': self.actions,
                'elevation': self.elevation,
                'padding': self.padding,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            },
            'children': self.children
        }


class DatametriaList:
    """
    Componente List DATAMETRIA.
    
    Lista otimizada com pull-to-refresh e paginação.
    """
    
    def __init__(
        self,
        data: List[Any],
        render_item: Callable[[Any, int], Dict[str, Any]],
        key_extractor: Optional[Callable[[Any, int], str]] = None,
        on_refresh: Optional[Callable] = None,
        refreshing: bool = False,
        on_end_reached: Optional[Callable] = None,
        loading_more: bool = False,
        empty_component: Optional[Dict[str, Any]] = None,
        **props
    ):
        self.data = data
        self.render_item = render_item
        self.key_extractor = key_extractor
        self.on_refresh = on_refresh
        self.refreshing = refreshing
        self.on_end_reached = on_end_reached
        self.loading_more = loading_more
        self.empty_component = empty_component
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaList initialized",
            items_count=len(data),
            has_refresh=bool(on_refresh),
            has_pagination=bool(on_end_reached)
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaList',
            'props': {
                'data': self.data,
                'renderItem': self.render_item,
                'keyExtractor': self.key_extractor,
                'onRefresh': self.on_refresh,
                'refreshing': self.refreshing,
                'onEndReached': self.on_end_reached,
                'loadingMore': self.loading_more,
                'emptyComponent': self.empty_component,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            }
        }


class DatametriaModal:
    """
    Componente Modal DATAMETRIA.
    
    Modal responsivo com animações e backdrop.
    """
    
    def __init__(
        self,
        visible: bool,
        on_close: Callable,
        title: Optional[str] = None,
        children: Optional[List[Any]] = None,
        size: str = 'md',
        animation_type: str = 'slide',
        backdrop_closable: bool = True,
        **props
    ):
        self.visible = visible
        self.on_close = on_close
        self.title = title
        self.children = children or []
        self.size = size
        self.animation_type = animation_type
        self.backdrop_closable = backdrop_closable
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaModal initialized",
            visible=visible,
            size=size,
            animation=animation_type
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaModal',
            'props': {
                'visible': self.visible,
                'onClose': self.on_close,
                'title': self.title,
                'size': self.size,
                'animationType': self.animation_type,
                'backdropClosable': self.backdrop_closable,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            },
            'children': self.children
        }


class DatametriaForm:
    """
    Componente Form DATAMETRIA.
    
    Formulário com validação integrada e estado gerenciado.
    """
    
    def __init__(
        self,
        on_submit: Callable[[Dict[str, Any]], None],
        validation_schema: Optional[Dict[str, Any]] = None,
        initial_values: Optional[Dict[str, Any]] = None,
        children: Optional[List[Any]] = None,
        **props
    ):
        self.on_submit = on_submit
        self.validation_schema = validation_schema
        self.initial_values = initial_values or {}
        self.children = children or []
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaForm initialized",
            has_validation=bool(validation_schema),
            initial_fields=len(initial_values)
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaForm',
            'props': {
                'onSubmit': self.on_submit,
                'validationSchema': self.validation_schema,
                'initialValues': self.initial_values,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            },
            'children': self.children
        }


class DatametriaHeader:
    """
    Componente Header DATAMETRIA.
    
    Header de navegação com ações e responsividade.
    """
    
    def __init__(
        self,
        title: str,
        show_back: bool = False,
        on_back: Optional[Callable] = None,
        right_action: Optional[Dict[str, Any]] = None,
        left_action: Optional[Dict[str, Any]] = None,
        subtitle: Optional[str] = None,
        **props
    ):
        self.title = title
        self.show_back = show_back
        self.on_back = on_back
        self.right_action = right_action
        self.left_action = left_action
        self.subtitle = subtitle
        self.props = ComponentProps(**props)
        
        logger.debug(
            "DatametriaHeader initialized",
            title=title,
            show_back=show_back,
            has_actions=bool(right_action or left_action)
        )
    
    def render_config(self) -> Dict[str, Any]:
        """Configuração de renderização."""
        return {
            'component': 'DatametriaHeader',
            'props': {
                'title': self.title,
                'showBack': self.show_back,
                'onBack': self.on_back,
                'rightAction': self.right_action,
                'leftAction': self.left_action,
                'subtitle': self.subtitle,
                'themeAware': self.props.theme_aware,
                'responsive': self.props.responsive,
                'testID': self.props.test_id
            }
        }


# Factory functions para facilitar uso
def create_screen(**kwargs) -> DatametriaScreen:
    """Criar DatametriaScreen."""
    return DatametriaScreen(**kwargs)

def create_button(**kwargs) -> DatametriaButton:
    """Criar DatametriaButton."""
    return DatametriaButton(**kwargs)

def create_input(**kwargs) -> DatametriaInput:
    """Criar DatametriaInput."""
    return DatametriaInput(**kwargs)

def create_card(**kwargs) -> DatametriaCard:
    """Criar DatametriaCard."""
    return DatametriaCard(**kwargs)

def create_list(**kwargs) -> DatametriaList:
    """Criar DatametriaList."""
    return DatametriaList(**kwargs)

def create_modal(**kwargs) -> DatametriaModal:
    """Criar DatametriaModal."""
    return DatametriaModal(**kwargs)

def create_form(**kwargs) -> DatametriaForm:
    """Criar DatametriaForm."""
    return DatametriaForm(**kwargs)

def create_header(**kwargs) -> DatametriaHeader:
    """Criar DatametriaHeader."""
    return DatametriaHeader(**kwargs)
