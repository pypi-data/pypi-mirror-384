import 'package:flutter/material.dart';
import 'datametria_theme.dart';

/// DATAMETRIA Loading Component with different variants
class DatametriaLoading extends StatelessWidget {
  final LoadingVariant variant;
  final String? message;
  final double? size;
  final Color? color;

  const DatametriaLoading({
    Key? key,
    this.variant = LoadingVariant.circular,
    this.message,
    this.size,
    this.color,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    final loadingColor = color ?? theme.colors.primary;
    
    Widget loadingWidget;
    
    switch (variant) {
      case LoadingVariant.circular:
        loadingWidget = SizedBox(
          width: size ?? 24,
          height: size ?? 24,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(loadingColor),
          ),
        );
        break;
      case LoadingVariant.linear:
        loadingWidget = LinearProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(loadingColor),
        );
        break;
      case LoadingVariant.dots:
        loadingWidget = _DotsLoading(color: loadingColor, size: size ?? 8);
        break;
    }

    if (message != null) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          loadingWidget,
          SizedBox(height: theme.spacing.medium),
          Text(
            message!,
            style: theme.textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ],
      );
    }

    return loadingWidget;
  }
}

enum LoadingVariant { circular, linear, dots }

/// Full screen loading overlay
class DatametriaLoadingOverlay extends StatelessWidget {
  final bool isLoading;
  final Widget child;
  final String? message;

  const DatametriaLoadingOverlay({
    Key? key,
    required this.isLoading,
    required this.child,
    this.message,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (isLoading)
          Container(
            color: Colors.black.withOpacity(0.5),
            child: Center(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: DatametriaLoading(
                    variant: LoadingVariant.circular,
                    message: message ?? 'Carregando...',
                    size: 32,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

/// Animated dots loading indicator
class _DotsLoading extends StatefulWidget {
  final Color color;
  final double size;

  const _DotsLoading({
    required this.color,
    required this.size,
  });

  @override
  State<_DotsLoading> createState() => _DotsLoadingState();
}

class _DotsLoadingState extends State<_DotsLoading>
    with TickerProviderStateMixin {
  late List<AnimationController> _controllers;
  late List<Animation<double>> _animations;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(3, (index) {
      return AnimationController(
        duration: const Duration(milliseconds: 600),
        vsync: this,
      );
    });

    _animations = _controllers.map((controller) {
      return Tween<double>(begin: 0.0, end: 1.0).animate(
        CurvedAnimation(parent: controller, curve: Curves.easeInOut),
      );
    }).toList();

    _startAnimations();
  }

  void _startAnimations() {
    for (int i = 0; i < _controllers.length; i++) {
      Future.delayed(Duration(milliseconds: i * 200), () {
        if (mounted) {
          _controllers[i].repeat(reverse: true);
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (index) {
        return AnimatedBuilder(
          animation: _animations[index],
          builder: (context, child) {
            return Container(
              margin: EdgeInsets.symmetric(horizontal: widget.size * 0.2),
              width: widget.size,
              height: widget.size,
              decoration: BoxDecoration(
                color: widget.color.withOpacity(_animations[index].value),
                shape: BoxShape.circle,
              ),
            );
          },
        );
      }),
    );
  }

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    super.dispose();
  }
}