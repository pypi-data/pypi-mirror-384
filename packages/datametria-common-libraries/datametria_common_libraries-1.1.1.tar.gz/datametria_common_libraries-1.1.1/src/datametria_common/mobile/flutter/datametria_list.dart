import 'package:flutter/material.dart';
import 'datametria_theme.dart';

/// DATAMETRIA List Component with pagination and error handling
class DatametriaList<T> extends StatefulWidget {
  final List<T> items;
  final Widget Function(T item, int index) itemBuilder;
  final bool isLoading;
  final String? errorMessage;
  final VoidCallback? onRetry;
  final VoidCallback? onLoadMore;
  final bool hasMore;
  final EdgeInsets? padding;

  const DatametriaList({
    Key? key,
    required this.items,
    required this.itemBuilder,
    this.isLoading = false,
    this.errorMessage,
    this.onRetry,
    this.onLoadMore,
    this.hasMore = false,
    this.padding,
  }) : super(key: key);

  @override
  State<DatametriaList<T>> createState() => _DatametriaListState<T>();
}

class _DatametriaListState<T> extends State<DatametriaList<T>> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= 
        _scrollController.position.maxScrollExtent - 200) {
      if (widget.hasMore && !widget.isLoading && widget.onLoadMore != null) {
        widget.onLoadMore!();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    
    if (widget.errorMessage != null) {
      return _buildErrorState(theme);
    }

    if (widget.items.isEmpty && !widget.isLoading) {
      return _buildEmptyState(theme);
    }

    return ListView.builder(
      controller: _scrollController,
      padding: widget.padding ?? EdgeInsets.all(theme.spacing.medium),
      itemCount: widget.items.length + (widget.isLoading ? 1 : 0),
      itemBuilder: (context, index) {
        if (index >= widget.items.length) {
          return _buildLoadingIndicator(theme);
        }
        return widget.itemBuilder(widget.items[index], index);
      },
    );
  }

  Widget _buildErrorState(DatametriaThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, 
               size: 64, 
               color: theme.colors.error),
          SizedBox(height: theme.spacing.medium),
          Text(widget.errorMessage!, 
               style: theme.textTheme.bodyLarge),
          if (widget.onRetry != null) ...[
            SizedBox(height: theme.spacing.medium),
            ElevatedButton(
              onPressed: widget.onRetry,
              child: const Text('Tentar Novamente'),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildEmptyState(DatametriaThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox_outlined, 
               size: 64, 
               color: theme.colors.onSurface.withOpacity(0.5)),
          SizedBox(height: theme.spacing.medium),
          Text('Nenhum item encontrado', 
               style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }

  Widget _buildLoadingIndicator(DatametriaThemeData theme) {
    return Padding(
      padding: EdgeInsets.all(theme.spacing.medium),
      child: const Center(child: CircularProgressIndicator()),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }
}