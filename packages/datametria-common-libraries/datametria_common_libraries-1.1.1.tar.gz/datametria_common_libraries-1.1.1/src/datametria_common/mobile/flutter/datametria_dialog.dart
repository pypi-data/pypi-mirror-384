import 'package:flutter/material.dart';
import 'datametria_theme.dart';
import 'datametria_button.dart';

/// DATAMETRIA Dialog Component with consistent styling
class DatametriaDialog extends StatelessWidget {
  final String title;
  final String? content;
  final Widget? contentWidget;
  final List<DatametriaDialogAction>? actions;
  final bool barrierDismissible;

  const DatametriaDialog({
    Key? key,
    required this.title,
    this.content,
    this.contentWidget,
    this.actions,
    this.barrierDismissible = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    
    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(theme.borderRadius.medium),
      ),
      title: Text(title, style: theme.textTheme.headlineSmall),
      content: contentWidget ?? (content != null ? Text(content!) : null),
      actions: actions?.map((action) => action.build(context)).toList(),
    );
  }

  static Future<T?> show<T>({
    required BuildContext context,
    required String title,
    String? content,
    Widget? contentWidget,
    List<DatametriaDialogAction>? actions,
    bool barrierDismissible = true,
  }) {
    return showDialog<T>(
      context: context,
      barrierDismissible: barrierDismissible,
      builder: (context) => DatametriaDialog(
        title: title,
        content: content,
        contentWidget: contentWidget,
        actions: actions,
        barrierDismissible: barrierDismissible,
      ),
    );
  }

  static Future<bool?> showConfirmation({
    required BuildContext context,
    required String title,
    required String content,
    String confirmText = 'Confirmar',
    String cancelText = 'Cancelar',
  }) {
    return show<bool>(
      context: context,
      title: title,
      content: content,
      actions: [
        DatametriaDialogAction(
          text: cancelText,
          onPressed: () => Navigator.of(context).pop(false),
        ),
        DatametriaDialogAction(
          text: confirmText,
          isPrimary: true,
          onPressed: () => Navigator.of(context).pop(true),
        ),
      ],
    );
  }
}

class DatametriaDialogAction {
  final String text;
  final VoidCallback onPressed;
  final bool isPrimary;
  final bool isDestructive;

  const DatametriaDialogAction({
    required this.text,
    required this.onPressed,
    this.isPrimary = false,
    this.isDestructive = false,
  });

  Widget build(BuildContext context) {
    if (isPrimary) {
      return DatametriaButton(
        text: text,
        onPressed: onPressed,
        variant: ButtonVariant.primary,
      );
    } else if (isDestructive) {
      return DatametriaButton(
        text: text,
        onPressed: onPressed,
        variant: ButtonVariant.outline,
        backgroundColor: Colors.red,
      );
    } else {
      return DatametriaButton(
        text: text,
        onPressed: onPressed,
        variant: ButtonVariant.text,
      );
    }
  }
}