import 'package:flutter/material.dart';
import '../../core/health_check.dart';
import '../../core/error_handler.dart';

enum DatametriaButtonVariant { primary, secondary, outline, text }
enum DatametriaButtonSize { small, medium, large }

class DatametriaButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final DatametriaButtonVariant variant;
  final DatametriaButtonSize size;
  final bool isLoading;
  final IconData? icon;

  const DatametriaButton({
    Key? key,
    required this.text,
    this.onPressed,
    this.variant = DatametriaButtonVariant.primary,
    this.size = DatametriaButtonSize.medium,
    this.isLoading = false,
    this.icon,
  }) : super(key: key);

  @override
  State<DatametriaButton> createState() => _DatametriaButtonState();
}

class _DatametriaButtonState extends State<DatametriaButton> with ErrorHandlerMixin {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return SizedBox(
      height: _getHeight(),
      child: ElevatedButton(
        onPressed: widget.isLoading ? null : _handlePress,
        style: _getButtonStyle(theme),
        child: widget.isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (widget.icon != null) ...[
                    Icon(widget.icon, size: _getIconSize()),
                    const SizedBox(width: 8),
                  ],
                  Text(widget.text, style: _getTextStyle()),
                ],
              ),
      ),
    );
  }

  void _handlePress() {
    try {
      widget.onPressed?.call();
    } catch (e) {
      handleError(e, ErrorCategory.SYSTEM, ErrorSeverity.LOW);
    }
  }

  double _getHeight() {
    switch (widget.size) {
      case DatametriaButtonSize.small:
        return 32;
      case DatametriaButtonSize.medium:
        return 40;
      case DatametriaButtonSize.large:
        return 48;
    }
  }

  double _getIconSize() {
    switch (widget.size) {
      case DatametriaButtonSize.small:
        return 16;
      case DatametriaButtonSize.medium:
        return 20;
      case DatametriaButtonSize.large:
        return 24;
    }
  }

  TextStyle _getTextStyle() {
    final fontSize = widget.size == DatametriaButtonSize.small ? 14.0 : 16.0;
    return TextStyle(fontSize: fontSize, fontWeight: FontWeight.w600);
  }

  ButtonStyle _getButtonStyle(ThemeData theme) {
    switch (widget.variant) {
      case DatametriaButtonVariant.primary:
        return ElevatedButton.styleFrom(
          backgroundColor: theme.colorScheme.primary,
          foregroundColor: theme.colorScheme.onPrimary,
        );
      case DatametriaButtonVariant.secondary:
        return ElevatedButton.styleFrom(
          backgroundColor: theme.colorScheme.secondary,
          foregroundColor: theme.colorScheme.onSecondary,
        );
      case DatametriaButtonVariant.outline:
        return OutlinedButton.styleFrom(
          foregroundColor: theme.colorScheme.primary,
          side: BorderSide(color: theme.colorScheme.primary),
        );
      case DatametriaButtonVariant.text:
        return TextButton.styleFrom(
          foregroundColor: theme.colorScheme.primary,
        );
    }
  }
}