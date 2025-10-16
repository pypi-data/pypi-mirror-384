import 'package:flutter/material.dart';
import '../../core/health_check.dart';
import '../../core/error_handler.dart';

class DatametriaScaffold extends StatefulWidget {
  final Widget body;
  final PreferredSizeWidget? appBar;
  final Widget? floatingActionButton;
  final Widget? drawer;
  final Widget? bottomNavigationBar;
  final bool showHealthIndicator;

  const DatametriaScaffold({
    Key? key,
    required this.body,
    this.appBar,
    this.floatingActionButton,
    this.drawer,
    this.bottomNavigationBar,
    this.showHealthIndicator = false,
  }) : super(key: key);

  @override
  State<DatametriaScaffold> createState() => _DatametriaScaffoldState();
}

class _DatametriaScaffoldState extends State<DatametriaScaffold> 
    with HealthCheckMixin, ErrorHandlerMixin {
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: widget.appBar,
      body: Stack(
        children: [
          widget.body,
          if (widget.showHealthIndicator)
            Positioned(
              top: 16,
              right: 16,
              child: _buildHealthIndicator(),
            ),
        ],
      ),
      floatingActionButton: widget.floatingActionButton,
      drawer: widget.drawer,
      bottomNavigationBar: widget.bottomNavigationBar,
    );
  }

  Widget _buildHealthIndicator() {
    return FutureBuilder<Map<String, dynamic>>(
      future: health_check(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const SizedBox.shrink();
        }

        final status = snapshot.data!['status'] as String;
        final color = status == 'healthy' 
            ? Colors.green 
            : status == 'degraded' 
                ? Colors.orange 
                : Colors.red;

        return Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        );
      },
    );
  }

  @override
  Future<Map<String, dynamic>> _check_component_health() async {
    return {
      'scaffold': true,
      'app_bar': widget.appBar != null,
      'body': true,
      'floating_action_button': widget.floatingActionButton != null,
    };
  }
}

class DatametriaAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool centerTitle;

  const DatametriaAppBar({
    Key? key,
    required this.title,
    this.actions,
    this.leading,
    this.centerTitle = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(title),
      centerTitle: centerTitle,
      actions: actions,
      leading: leading,
      elevation: 0,
      backgroundColor: Theme.of(context).colorScheme.surface,
      foregroundColor: Theme.of(context).colorScheme.onSurface,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}