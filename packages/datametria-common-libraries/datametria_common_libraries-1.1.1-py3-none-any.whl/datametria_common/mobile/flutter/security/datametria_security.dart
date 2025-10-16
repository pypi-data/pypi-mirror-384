import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto/crypto.dart';

class DatametriaSecurityManager {
  final String appId;
  final Map<String, dynamic> config;
  final LocalAuthentication _localAuth = LocalAuthentication();
  final FlutterSecureStorage _secureStorage;

  DatametriaSecurityManager({
    required this.appId,
    required this.config,
  }) : _secureStorage = FlutterSecureStorage(
          aOptions: AndroidOptions(
            encryptedSharedPreferences: true,
          ),
          iOptions: IOSOptions(
            accessibility: IOSAccessibility.first_unlock_this_device,
          ),
        );

  Future<bool> authenticateBiometric({
    String reason = 'Autenticação necessária para continuar',
    bool biometricOnly = false,
  }) async {
    try {
      final bool isAvailable = await _localAuth.canCheckBiometrics;
      if (!isAvailable) return false;

      final List<BiometricType> availableBiometrics = 
          await _localAuth.getAvailableBiometrics();
      
      if (availableBiometrics.isEmpty) return false;

      final bool didAuthenticate = await _localAuth.authenticate(
        localizedReason: reason,
        options: AuthenticationOptions(
          biometricOnly: biometricOnly,
          stickyAuth: true,
        ),
      );

      return didAuthenticate;
    } catch (e) {
      return false;
    }
  }

  Future<bool> storeSecure(
    String key, 
    String value, 
    {String securityLevel = 'medium'}
  ) async {
    try {
      final String secureKey = 'datametria_${appId}_$key';
      
      String finalValue = value;
      if (config['encryption']['enabled'] == true) {
        finalValue = _encryptData(value);
      }

      await _secureStorage.write(
        key: secureKey,
        value: finalValue,
      );

      return true;
    } catch (e) {
      return false;
    }
  }

  Future<String?> retrieveSecure(String key) async {
    try {
      final String secureKey = 'datametria_${appId}_$key';
      
      final String? value = await _secureStorage.read(key: secureKey);
      
      if (value == null) return null;

      if (config['encryption']['enabled'] == true) {
        return _decryptData(value);
      }

      return value;
    } catch (e) {
      return null;
    }
  }

  Future<bool> removeSecure(String key) async {
    try {
      final String secureKey = 'datametria_${appId}_$key';
      await _secureStorage.delete(key: secureKey);
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<String> getDeviceFingerprint() async {
    try {
      final Map<String, dynamic> deviceInfo = {
        'platform': Platform.operatingSystem,
        'version': Platform.operatingSystemVersion,
        'appId': appId,
      };

      final String deviceString = json.encode(deviceInfo);
      final List<int> bytes = utf8.encode(deviceString);
      final Digest digest = sha256.convert(bytes);
      
      return digest.toString();
    } catch (e) {
      return '';
    }
  }

  Future<bool> isDeviceCompromised() async {
    try {
      return false; // Simplified implementation
    } catch (e) {
      return false;
    }
  }

  bool validateCertificate(String certificate) {
    try {
      final List<String> pinnedCerts = 
          List<String>.from(config['networking']['pinnedCertificates'] ?? []);
      
      return pinnedCerts.contains(certificate);
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, String>> getSecurityHeaders() async {
    final String deviceFingerprint = await getDeviceFingerprint();
    final String timestamp = DateTime.now().millisecondsSinceEpoch.toString();
    
    return {
      'X-App-ID': appId,
      'X-Device-Fingerprint': deviceFingerprint,
      'X-Timestamp': timestamp,
      'X-Platform': Platform.operatingSystem,
    };
  }

  String _encryptData(String data) {
    final List<int> bytes = utf8.encode(data);
    return base64.encode(bytes);
  }

  String _decryptData(String encryptedData) {
    final List<int> bytes = base64.decode(encryptedData);
    return utf8.decode(bytes);
  }
}

enum SecurityLevel {
  low,
  medium,
  high,
  critical,
}