const keyGenParams = {
  name: 'RSA-OAEP',
  modulusLength: 2048,
  publicExponent: new Uint8Array([1, 0, 1]),
  hash: 'SHA-256',
};

const aesKeyGenParams = {
  name: 'AES-GCM',
  length: 256,
};

/**
 * Converts a PEM string to an ArrayBuffer.
 * @param {string} pem - The PEM formatted string.
 * @returns {ArrayBuffer}
 */
function pemToArrayBuffer(pem) {
  const base64 = pem.trim().split('\n').slice(1, -1).join('');
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Generates an RSA-OAEP key pair for encryption.
 * @returns {Promise<CryptoKeyPair>}
 */
async function generateRsaKeyPair() {
  return window.crypto.subtle.generateKey(keyGenParams, true, ['encrypt', 'decrypt']);
}

/**
 * Exports a CryptoKey to a PEM-like string format.
 * @param {string} format - 'spki' for public key, 'pkcs8' for private key.
 * @param {CryptoKey} key - The key to export.
 * @returns {Promise<string>}
 */
async function exportKeyToPem(format, key) {
  const exported = await window.crypto.subtle.exportKey(format, key);
  const exportedAsString = String.fromCharCode.apply(null, new Uint8Array(exported));
  const exportedAsBase64 = window.btoa(exportedAsString);
  const header = format === 'spki' ? 'PUBLIC KEY' : 'PRIVATE KEY';
  return `-----BEGIN ${header}-----\n${exportedAsBase64}\n-----END ${header}-----`;
}

/**
 * Imports a PEM-formatted public key.
 * @param {string} pem - The PEM string.
 * @returns {Promise<CryptoKey>}
 */
async function importPublicKey(pem) {
  const buffer = pemToArrayBuffer(pem);
  return window.crypto.subtle.importKey('spki', buffer, keyGenParams, true, ['encrypt']);
}

/**
 * Imports a PEM-formatted private key.
 * @param {string} pem - The PEM string.
 * @returns {Promise<CryptoKey>}
 */
async function importPrivateKey(pem) {
  const buffer = pemToArrayBuffer(pem);
  return window.crypto.subtle.importKey('pkcs8', buffer, keyGenParams, true, ['decrypt']);
}

/**
 * Generates a symmetric AES-GCM key.
 * @returns {Promise<CryptoKey>}
 */
async function generateSymmetricKey() {
  return window.crypto.subtle.generateKey(aesKeyGenParams, true, ['encrypt', 'decrypt']);
}

/**
 * Encrypts data with an RSA public key.
 * @param {CryptoKey} publicKey - The public key to encrypt with.
 * @param {ArrayBuffer} data - The data to encrypt.
 * @returns {Promise<ArrayBuffer>} - The encrypted data.
 */
async function encryptWithPublicKey(publicKey, data) {
    return window.crypto.subtle.encrypt(keyGenParams, publicKey, data);
}

/**
 * Decrypts data with an RSA private key.
 * @param {CryptoKey} privateKey - The private key to decrypt with.
 * @param {ArrayBuffer} encryptedData - The data to decrypt.
 * @returns {Promise<ArrayBuffer>} - The decrypted data.
 */
async function decryptWithPrivateKey(privateKey, encryptedData) {
    return window.crypto.subtle.decrypt(keyGenParams, privateKey, encryptedData);
}

/**
 * Encrypts a message with a symmetric key using AES-GCM.
 * @param {CryptoKey} key - The symmetric key.
 * @param {string} plaintext - The message to encrypt.
 * @returns {Promise<{iv: Uint8Array, ciphertext: ArrayBuffer}>}
 */
async function encryptSymmetric(key, plaintext) {
    const iv = window.crypto.getRandomValues(new Uint8Array(12)); // GCM standard IV size
    const encodedPlaintext = new TextEncoder().encode(plaintext);
    const ciphertext = await window.crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        key,
        encodedPlaintext
    );
    return { iv, ciphertext };
}

/**
 * Decrypts a message with a symmetric key using AES-GCM.
 * @param {CryptoKey} key - The symmetric key.
 * @param {ArrayBuffer} ciphertext - The encrypted data.
 * @param {Uint8Array} iv - The initialization vector.
 * @returns {Promise<string>} - The decrypted plaintext.
 */
async function decryptSymmetric(key, ciphertext, iv) {
    const decrypted = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
    );
    return new TextDecoder().decode(decrypted);
}

export {
  generateRsaKeyPair,
  exportKeyToPem,
  importPublicKey,
  importPrivateKey,
  generateSymmetricKey,
  encryptWithPublicKey,
  decryptWithPrivateKey,
  encryptSymmetric,
  decryptSymmetric
}; 