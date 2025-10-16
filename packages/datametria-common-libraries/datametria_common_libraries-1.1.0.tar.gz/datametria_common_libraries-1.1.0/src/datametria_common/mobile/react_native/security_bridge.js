/**
 * DATAMETRIA React Native Security Bridge
 * 
 * Native bridge for React Native security features including
 * biometric authentication, secure storage, and certificate pinning.
 */

import { NativeModules, Platform } from 'react-native';
import Keychain from '@react-native-keychain/react-native-keychain';
import TouchID from 'react-native-touch-id';

class DatametriaSecurityBridge {
  constructor(config) {
    this.config = config.securityConfig;
    this.appId = this.config.appId;
    this.keyPrefix = this.config.secureStorage.keyPrefix;
  }

  /**
   * Authenticate using biometric data
   */
  async authenticateBiometric(type = 'fingerprint') {
    try {
      const biometricOptions = {
        title: 'Autenticação Biométrica',
        subtitle: 'Use sua biometria para continuar',
        description: 'Coloque seu dedo no sensor ou olhe para a câmera',
        fallbackLabel: 'Usar senha',
        cancelLabel: 'Cancelar',
      };

      if (Platform.OS === 'ios') {
        return await TouchID.authenticate('Autenticação necessária', biometricOptions);
      } else {
        // Android biometric authentication
        const { available, biometryType } = await TouchID.isSupported();
        if (available) {
          return await TouchID.authenticate('Autenticação necessária', biometricOptions);
        }
        return false;
      }
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  }

  /**
   * Store data securely in keychain/keystore
   */
  async storeSecure(key, value, securityLevel = 'medium') {
    try {
      const secureKey = `${this.keyPrefix}_${key}`;
      
      const options = {
        accessControl: this._getAccessControl(securityLevel),
        authenticationType: this._getAuthenticationType(securityLevel),
        accessGroup: this.appId,
        touchID: securityLevel === 'high' || securityLevel === 'critical',
        showModal: true,
      };

      await Keychain.setInternetCredentials(
        secureKey,
        key,
        value,
        options
      );
      
      return true;
    } catch (error) {
      console.error('Secure storage failed:', error);
      return false;
    }
  }

  /**
   * Retrieve secure data from keychain/keystore
   */
  async retrieveSecure(key) {
    try {
      const secureKey = `${this.keyPrefix}_${key}`;
      
      const credentials = await Keychain.getInternetCredentials(secureKey);
      
      if (credentials && credentials.password) {
        return credentials.password;
      }
      
      return null;
    } catch (error) {
      console.error('Secure retrieval failed:', error);
      return null;
    }
  }

  /**
   * Remove secure data
   */
  async removeSecure(key) {
    try {
      const secureKey = `${this.keyPrefix}_${key}`;
      return await Keychain.resetInternetCredentials(secureKey);
    } catch (error) {
      console.error('Secure removal failed:', error);
      return false;
    }
  }

  /**
   * Validate SSL certificate (certificate pinning)
   */
  validateCertificate(certificate) {
    // Certificate pinning validation
    const pinnedCertificates = this.config.certificatePinning.pins || [];
    return pinnedCertificates.includes(certificate);
  }

  /**
   * Generate device fingerprint
   */
  async getDeviceFingerprint() {
    try {
      const deviceInfo = {
        platform: Platform.OS,
        version: Platform.Version,
        appId: this.appId,
      };
      
      // Simple fingerprint generation
      const fingerprint = btoa(JSON.stringify(deviceInfo));
      return fingerprint;
    } catch (error) {
      console.error('Device fingerprint generation failed:', error);
      return null;
    }
  }

  /**
   * Check if device is rooted/jailbroken
   */
  async isDeviceCompromised() {
    try {
      // Simplified root/jailbreak detection
      if (Platform.OS === 'ios') {
        // Check for jailbreak indicators
        return false; // Would implement actual detection
      } else {
        // Check for root indicators
        return false; // Would implement actual detection
      }
    } catch (error) {
      return false;
    }
  }

  /**
   * Get security headers for API requests
   */
  async getSecurityHeaders() {
    const deviceFingerprint = await this.getDeviceFingerprint();
    const timestamp = Date.now().toString();
    
    return {
      'X-App-ID': this.appId,
      'X-Device-Fingerprint': deviceFingerprint,
      'X-Timestamp': timestamp,
      'X-Platform': Platform.OS,
    };
  }

  /**
   * Get access control level based on security level
   */
  _getAccessControl(securityLevel) {
    switch (securityLevel) {
      case 'critical':
        return Keychain.ACCESS_CONTROL.BIOMETRY_CURRENT_SET;
      case 'high':
        return Keychain.ACCESS_CONTROL.BIOMETRY_ANY;
      case 'medium':
        return Keychain.ACCESS_CONTROL.DEVICE_PASSCODE;
      default:
        return Keychain.ACCESS_CONTROL.WHEN_UNLOCKED;
    }
  }

  /**
   * Get authentication type based on security level
   */
  _getAuthenticationType(securityLevel) {
    switch (securityLevel) {
      case 'critical':
      case 'high':
        return Keychain.AUTHENTICATION_TYPE.BIOMETRICS;
      case 'medium':
        return Keychain.AUTHENTICATION_TYPE.DEVICE_PASSCODE_OR_BIOMETRICS;
      default:
        return Keychain.AUTHENTICATION_TYPE.DEVICE_PASSCODE;
    }
  }
}

export default DatametriaSecurityBridge;