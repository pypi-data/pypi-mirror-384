import 'package:flutter/material.dart';
import 'datametria_theme.dart';

/// DATAMETRIA Bottom Navigation Bar
class DatametriaBottomNavigation extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<DatametriaNavItem> items;

  const DatametriaBottomNavigation({
    Key? key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    
    return BottomNavigationBar(
      currentIndex: currentIndex,
      onTap: onTap,
      type: BottomNavigationBarType.fixed,
      selectedItemColor: theme.colors.primary,
      unselectedItemColor: theme.colors.onSurface.withOpacity(0.6),
      items: items.map((item) => BottomNavigationBarItem(
        icon: Icon(item.icon),
        activeIcon: Icon(item.activeIcon ?? item.icon),
        label: item.label,
      )).toList(),
    );
  }
}

class DatametriaNavItem {
  final IconData icon;
  final IconData? activeIcon;
  final String label;

  const DatametriaNavItem({
    required this.icon,
    required this.label,
    this.activeIcon,
  });
}

/// DATAMETRIA Drawer Navigation
class DatametriaDrawer extends StatelessWidget {
  final String? userEmail;
  final String? userName;
  final Widget? userAvatar;
  final List<DatametriaDrawerItem> items;
  final VoidCallback? onLogout;

  const DatametriaDrawer({
    Key? key,
    this.userEmail,
    this.userName,
    this.userAvatar,
    required this.items,
    this.onLogout,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = DatametriaTheme.of(context);
    
    return Drawer(
      child: Column(
        children: [
          if (userName != null || userEmail != null)
            UserAccountsDrawerHeader(
              accountName: userName != null ? Text(userName!) : null,
              accountEmail: userEmail != null ? Text(userEmail!) : null,
              currentAccountPicture: userAvatar ?? CircleAvatar(
                backgroundColor: theme.colors.primary,
                child: Icon(Icons.person, color: theme.colors.onPrimary),
              ),
              decoration: BoxDecoration(color: theme.colors.primary),
            ),
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: items.map((item) => _buildDrawerItem(context, item)).toList(),
            ),
          ),
          if (onLogout != null) ...[
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Sair'),
              onTap: onLogout,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDrawerItem(BuildContext context, DatametriaDrawerItem item) {
    if (item.children != null && item.children!.isNotEmpty) {
      return ExpansionTile(
        leading: Icon(item.icon),
        title: Text(item.title),
        children: item.children!
            .map((child) => Padding(
                  padding: const EdgeInsets.only(left: 16),
                  child: _buildDrawerItem(context, child),
                ))
            .toList(),
      );
    }

    return ListTile(
      leading: Icon(item.icon),
      title: Text(item.title),
      onTap: () {
        Navigator.pop(context);
        item.onTap?.call();
      },
    );
  }
}

class DatametriaDrawerItem {
  final IconData icon;
  final String title;
  final VoidCallback? onTap;
  final List<DatametriaDrawerItem>? children;

  const DatametriaDrawerItem({
    required this.icon,
    required this.title,
    this.onTap,
    this.children,
  });
}