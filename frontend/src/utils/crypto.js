/**
 * 加密模块配置参数
 */

// RSA-OAEP密钥生成参数
const keyGenParams = {
  name: 'RSA-OAEP',  // 使用RSA-OAEP算法
  modulusLength: 2048, // 密钥长度2048位
  publicExponent: new Uint8Array([1, 0, 1]), // 公钥指数65537
  hash: 'SHA-256', // 使用SHA-256哈希算法
};

// AES-GCM密钥生成参数
const aesKeyGenParams = {
  name: 'AES-GCM', // 使用AES-GCM算法
  length: 256, // 密钥长度256位
};

/**
 * 将PEM字符串转换为ArrayBuffer。
 * @param {string} pem - PEM格式字符串。
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
 * 生成RSA-OAEP加密用的密钥对。
 * @returns {Promise<CryptoKeyPair>}
 */
async function generateRsaKeyPair() {
  return window.crypto.subtle.generateKey(keyGenParams, true, ['encrypt', 'decrypt']);
}

/**
 * 导出CryptoKey为PEM格式字符串。
 * @param {string} format - spki为公钥，pkcs8为私钥。
 * @param {CryptoKey} key - 要导出的密钥。
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
 * 导入PEM格式的公钥。
 * @param {string} pem - PEM字符串。
 * @returns {Promise<CryptoKey>}
 */
async function importPublicKey(pem) {
  const buffer = pemToArrayBuffer(pem);
  return window.crypto.subtle.importKey('spki', buffer, keyGenParams, true, ['encrypt']);
}

/**
 * 导入PEM格式的私钥。
 * @param {string} pem - PEM字符串。
 * @returns {Promise<CryptoKey>}
 */
async function importPrivateKey(pem) {
  const buffer = pemToArrayBuffer(pem);
  return window.crypto.subtle.importKey('pkcs8', buffer, keyGenParams, true, ['decrypt']);
}

/**
 * 生成对称AES-GCM密钥。
 * @returns {Promise<CryptoKey>}
 */
async function generateSymmetricKey() {
  return window.crypto.subtle.generateKey(aesKeyGenParams, true, ['encrypt', 'decrypt']);
}

/**
 * 使用RSA公钥加密数据。
 * @param {CryptoKey} publicKey - 用于加密的公钥。
 * @param {ArrayBuffer} data - 要加密的数据。
 * @returns {Promise<ArrayBuffer>} - 加密后的数据。
 */
async function encryptWithPublicKey(publicKey, data) {
  return window.crypto.subtle.encrypt(keyGenParams, publicKey, data);
}

/**
 * 使用RSA私钥解密数据。
 * @param {CryptoKey} privateKey - 用于解密的私钥。
 * @param {ArrayBuffer} encryptedData - 要解密的数据。
 * @returns {Promise<ArrayBuffer>} - 解密后的数据。
 */
async function decryptWithPrivateKey(privateKey, encryptedData) {
  return window.crypto.subtle.decrypt(keyGenParams, privateKey, encryptedData);
}

/**
 * 使用对称密钥（AES-GCM）加密消息。
 * @param {CryptoKey} key - 对称密钥。
 * @param {string} plaintext - 要加密的明文。
 * @returns {Promise<{iv: Uint8Array, ciphertext: ArrayBuffer}>}
 */
async function encryptSymmetric(key, plaintext) {
  const iv = window.crypto.getRandomValues(new Uint8Array(12)); // 标准IV长度
  const encodedPlaintext = new TextEncoder().encode(plaintext);
  const ciphertext = await window.crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encodedPlaintext
  );
  return { iv, ciphertext };
}

/**
 * 使用对称密钥（AES-GCM）解密消息。
 * @param {CryptoKey} key - 对称密钥。
 * @param {ArrayBuffer} ciphertext - 加密数据。
 * @param {Uint8Array} iv - 初始化向量。
 * @returns {Promise<string>} - 解密后的明文。
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