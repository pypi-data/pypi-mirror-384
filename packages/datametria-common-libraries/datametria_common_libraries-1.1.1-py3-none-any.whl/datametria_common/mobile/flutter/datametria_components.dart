/// DATAMETRIA Flutter Components Library
/// 
/// Complete set of Flutter components following DATAMETRIA design standards
/// with foundation mixin integration for health checks and error handling.

library datametria_components;

// Core Theme
export 'datametria_theme.dart';

// UI Components
export 'datametria_button.dart';
export 'datametria_input.dart';
export 'datametria_card.dart';
export 'datametria_list.dart';
export 'datametria_dialog.dart';
export 'datametria_form.dart';
export 'datametria_loading.dart';
export 'datametria_snackbar.dart';

// Layout Components
export 'datametria_scaffold.dart';
export 'datametria_navigation.dart';

/// DATAMETRIA Components Version
const String datametriaComponentsVersion = '1.0.0';

/// Component Usage Statistics
class DatametriaComponentsStats {
  static int _buttonUsage = 0;
  static int _inputUsage = 0;
  static int _cardUsage = 0;
  static int _listUsage = 0;
  static int _dialogUsage = 0;
  static int _formUsage = 0;
  
  static void incrementButtonUsage() => _buttonUsage++;
  static void incrementInputUsage() => _inputUsage++;
  static void incrementCardUsage() => _cardUsage++;
  static void incrementListUsage() => _listUsage++;
  static void incrementDialogUsage() => _dialogUsage++;
  static void incrementFormUsage() => _formUsage++;
  
  static Map<String, int> getStats() => {
    'button': _buttonUsage,
    'input': _inputUsage,
    'card': _cardUsage,
    'list': _listUsage,
    'dialog': _dialogUsage,
    'form': _formUsage,
  };
  
  static void resetStats() {
    _buttonUsage = 0;
    _inputUsage = 0;
    _cardUsage = 0;
    _listUsage = 0;
    _dialogUsage = 0;
    _formUsage = 0;
  }
}