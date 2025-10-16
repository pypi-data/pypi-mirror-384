import 'package:flutter/material.dart';
import 'datametria_theme.dart';

/// DATAMETRIA SnackBar Component with different types
class DatametriaSnackBar {
  static void show({
    required BuildContext context,
    required String message,
    SnackBarType type = SnackBarType.info,
    Duration duration = const Duration(seconds: 4),
    String? actionLabel,
    VoidCallback? onAction,
  }) {
    final theme = DatametriaTheme.of(context);
    final colors = _getColorsForType(type, theme);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              _getIconForType(type),
              color: colors.onBackground,
              size: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: colors.onBackground),
              ),
            ),
          ],
        ),
        backgroundColor: colors.background,
        duration: duration,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(theme.borderRadius.small),
        ),
        action: actionLabel != null && onAction != null
            ? SnackBarAction(
                label: actionLabel,
                textColor: colors.onBackground,
                onPressed: onAction,
              )
            : null,
      ),
    );
  }

  static void showSuccess({
    required BuildContext context,
    required String message,
    Duration duration = const Duration(seconds: 3),
  }) {
    show(
      context: context,
      message: message,
      type: SnackBarType.success,
      duration: duration,
    );
  }

  static void showError({
    required BuildContext context,
    required String message,
    Duration duration = const Duration(seconds: 5),
    String? actionLabel,
    VoidCallback? onAction,
  }) {
    show(
      context: context,
      message: message,
      type: SnackBarType.error,
      duration: duration,
      actionLabel: actionLabel,
      onAction: onAction,
    );
  }

  static void showWarning({
    required BuildContext context,
    required String message,
    Duration duration = const Duration(seconds: 4),
  }) {
    show(
      context: context,
      message: message,
      type: SnackBarType.warning,
      duration: duration,
    );
  }

  static void showInfo({
    required BuildContext context,
    required String message,
    Duration duration = const Duration(seconds: 3),
  }) {
    show(
      context: context,
      message: message,
      type: SnackBarType.info,
      duration: duration,
    );
  }

  static _SnackBarColors _getColorsForType(SnackBarType type, DatametriaThemeData theme) {
    switch (type) {
      case SnackBarType.success:
        return _SnackBarColors(
          background: const Color(0xFF4CAF50),
          onBackground: Colors.white,
        );
      case SnackBarType.error:
        return _SnackBarColors(
          background: theme.colors.error,
          onBackground: Colors.white,
        );
      case SnackBarType.warning:
        return _SnackBarColors(
          background: const Color(0xFFFF9800),
          onBackground: Colors.white,
        );
      case SnackBarType.info:
        return _SnackBarColors(
          background: theme.colors.primary,
          onBackground: Colors.white,
        );
    }
  }

  static IconData _getIconForType(SnackBarType type) {
    switch (type) {
      case SnackBarType.success:
        return Icons.check_circle_outline;
      case SnackBarType.error:
        return Icons.error_outline;
      case SnackBarType.warning:
        return Icons.warning_amber_outlined;
      case SnackBarType.info:
        return Icons.info_outline;
    }
  }
}

enum SnackBarType { success, error, warning, info }

class _SnackBarColors {
  final Color background;
  final Color onBackground;

  const _SnackBarColors({
    required this.background,
    required this.onBackground,
  });
}