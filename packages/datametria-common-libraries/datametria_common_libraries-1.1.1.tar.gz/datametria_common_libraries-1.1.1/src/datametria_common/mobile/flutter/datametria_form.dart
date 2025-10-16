import 'package:flutter/material.dart';
import 'datametria_theme.dart';
import 'datametria_button.dart';

/// DATAMETRIA Form Component with validation and error handling
class DatametriaForm extends StatefulWidget {
  final Widget child;
  final VoidCallback? onSubmit;
  final String? submitText;
  final bool isLoading;
  final GlobalKey<FormState>? formKey;

  const DatametriaForm({
    Key? key,
    required this.child,
    this.onSubmit,
    this.submitText,
    this.isLoading = false,
    this.formKey,
  }) : super(key: key);

  @override
  State<DatametriaForm> createState() => _DatametriaFormState();
}

class _DatametriaFormState extends State<DatametriaForm> {
  late GlobalKey<FormState> _formKey;

  @override
  void initState() {
    super.initState();
    _formKey = widget.formKey ?? GlobalKey<FormState>();
  }

  void _handleSubmit() {
    if (_formKey.currentState?.validate() ?? false) {
      widget.onSubmit?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          widget.child,
          if (widget.onSubmit != null) ...[
            SizedBox(height: theme.spacing.large),
            DatametriaButton(
              text: widget.submitText ?? 'Enviar',
              onPressed: widget.isLoading ? null : _handleSubmit,
              isLoading: widget.isLoading,
              variant: ButtonVariant.primary,
            ),
          ],
        ],
      ),
    );
  }
}

/// Form field wrapper with consistent styling
class DatametriaFormField extends StatelessWidget {
  final String label;
  final Widget child;
  final String? helperText;
  final bool isRequired;

  const DatametriaFormField({
    Key? key,
    required this.label,
    required this.child,
    this.helperText,
    this.isRequired = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label,
              style: theme.textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            if (isRequired)
              Text(
                ' *',
                style: TextStyle(color: theme.colors.error),
              ),
          ],
        ),
        SizedBox(height: theme.spacing.small),
        child,
        if (helperText != null) ...[
          SizedBox(height: theme.spacing.small),
          Text(
            helperText!,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colors.onSurface.withOpacity(0.6),
            ),
          ),
        ],
        SizedBox(height: theme.spacing.medium),
      ],
    );
  }
}