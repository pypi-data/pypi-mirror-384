import 'package:flutter/material.dart';
import '../datametria_components.dart';

void main() {
  runApp(const DatametriaExampleApp());
}

class DatametriaExampleApp extends StatelessWidget {
  const DatametriaExampleApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DATAMETRIA Components Example',
      theme: DatametriaTheme.lightTheme,
      darkTheme: DatametriaTheme.darkTheme,
      themeMode: ThemeMode.system,
      home: const ExampleHomePage(),
    );
  }
}

class ExampleHomePage extends StatefulWidget {
  const ExampleHomePage({Key? key}) : super(key: key);

  @override
  State<ExampleHomePage> createState() => _ExampleHomePageState();
}

class _ExampleHomePageState extends State<ExampleHomePage> {
  int _currentIndex = 0;
  bool _isLoading = false;
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();

  final List<String> _items = List.generate(20, (index) => 'Item ${index + 1}');

  @override
  Widget build(BuildContext context) {
    return DatametriaScaffold(
      appBar: DatametriaAppBar(
        title: 'DATAMETRIA Components',
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showInfoDialog,
          ),
        ],
      ),
      drawer: DatametriaDrawer(
        userName: 'Usuário Demo',
        userEmail: 'demo@datametria.io',
        items: [
          DatametriaDrawerItem(
            icon: Icons.home,
            title: 'Início',
            onTap: () => _showSnackBar('Início selecionado'),
          ),
          DatametriaDrawerItem(
            icon: Icons.settings,
            title: 'Configurações',
            onTap: () => _showSnackBar('Configurações selecionadas'),
          ),
        ],
        onLogout: () => _showSnackBar('Logout realizado'),
      ),
      body: DatametriaLoadingOverlay(
        isLoading: _isLoading,
        message: 'Processando...',
        child: _buildCurrentPage(),
      ),
      bottomNavigationBar: DatametriaBottomNavigation(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        items: [
          DatametriaNavItem(icon: Icons.home, label: 'Início'),
          DatametriaNavItem(icon: Icons.list, label: 'Lista'),
          DatametriaNavItem(icon: Icons.form_control_label, label: 'Formulário'),
        ],
      ),
    );
  }

  Widget _buildCurrentPage() {
    switch (_currentIndex) {
      case 0:
        return _buildHomePage();
      case 1:
        return _buildListPage();
      case 2:
        return _buildFormPage();
      default:
        return _buildHomePage();
    }
  }

  Widget _buildHomePage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          DatametriaCard(
            title: 'Bem-vindo aos Componentes DATAMETRIA',
            content: 'Esta é uma demonstração dos componentes Flutter seguindo os padrões DATAMETRIA.',
            actions: [
              DatametriaButton(
                text: 'Explorar',
                onPressed: () => setState(() => _currentIndex = 1),
                variant: ButtonVariant.primary,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: DatametriaButton(
                  text: 'Sucesso',
                  onPressed: () => DatametriaSnackBar.showSuccess(
                    context: context,
                    message: 'Operação realizada com sucesso!',
                  ),
                  variant: ButtonVariant.primary,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: DatametriaButton(
                  text: 'Erro',
                  onPressed: () => DatametriaSnackBar.showError(
                    context: context,
                    message: 'Erro simulado',
                    actionLabel: 'Tentar Novamente',
                    onAction: () => _showSnackBar('Tentando novamente...'),
                  ),
                  variant: ButtonVariant.outline,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          DatametriaButton(
            text: 'Loading Demo',
            isLoading: _isLoading,
            onPressed: _isLoading ? null : _simulateLoading,
            variant: ButtonVariant.secondary,
          ),
        ],
      ),
    );
  }

  Widget _buildListPage() {
    return DatametriaList<String>(
      items: _items,
      itemBuilder: (item, index) => DatametriaListCard(
        title: item,
        subtitle: 'Descrição do $item',
        trailing: const Icon(Icons.chevron_right),
        onTap: () => _showSnackBar('$item selecionado'),
      ),
    );
  }

  Widget _buildFormPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: DatametriaForm(
        formKey: _formKey,
        onSubmit: _handleFormSubmit,
        submitText: 'Salvar Dados',
        isLoading: _isLoading,
        child: Column(
          children: [
            DatametriaFormField(
              label: 'Nome Completo',
              isRequired: true,
              helperText: 'Digite seu nome completo',
              child: DatametriaInput(
                controller: _nameController,
                validator: (value) => value?.isEmpty == true ? 'Campo obrigatório' : null,
              ),
            ),
            DatametriaFormField(
              label: 'Email',
              isRequired: true,
              helperText: 'Será usado para contato',
              child: DatametriaInput(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                validator: _validateEmail,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showInfoDialog() {
    DatametriaDialog.show(
      context: context,
      title: 'Sobre os Componentes',
      content: 'Esta é uma demonstração dos componentes DATAMETRIA Flutter v1.0.0',
      actions: [
        DatametriaDialogAction(
          text: 'Fechar',
          onPressed: () => Navigator.of(context).pop(),
        ),
      ],
    );
  }

  void _simulateLoading() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 2));
    setState(() => _isLoading = false);
    _showSnackBar('Operação concluída!');
  }

  void _handleFormSubmit() async {
    if (_formKey.currentState?.validate() ?? false) {
      setState(() => _isLoading = true);
      await Future.delayed(const Duration(seconds: 1));
      setState(() => _isLoading = false);
      
      DatametriaSnackBar.showSuccess(
        context: context,
        message: 'Formulário salvo com sucesso!',
      );
      
      _nameController.clear();
      _emailController.clear();
    }
  }

  String? _validateEmail(String? value) {
    if (value?.isEmpty == true) return 'Campo obrigatório';
    if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value!)) {
      return 'Email inválido';
    }
    return null;
  }

  void _showSnackBar(String message) {
    DatametriaSnackBar.showInfo(
      context: context,
      message: message,
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    super.dispose();
  }
}