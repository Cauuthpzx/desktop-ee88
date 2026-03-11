#pragma once

#include <QByteArray>
#include <QString>

// ============================================================================
// UpstreamCrypto — AES-ECB encrypt/decrypt + RSA + reverseChunks
// Port từ Go: Goserver/pkg/utils/agent_encrypt.go
// ============================================================================

namespace UpstreamCrypto {

// reverseChunks — obfuscation algorithm (tự inverse).
// Chunk sizes cycle: 2, 3, 4, 5, 6, 7, 8, 2, 3, ...
QString reverse_chunks(const QString& input);

// Decode encrypt_public_key từ upstream → PEM RSA public key.
// Input: base64 encoded + reverseChunks obfuscated.
QString decode_encrypt_public_key(const QString& encoded_key);

// Generate random 16-char alphanumeric AES key.
QByteArray generate_aes_key();

// AES-ECB encrypt plaintext → base64 ciphertext.
// Key phải 16 bytes.
QByteArray aes_ecb_encrypt(const QByteArray& plaintext, const QByteArray& key);

// AES-ECB decrypt base64 ciphertext → plaintext.
QByteArray aes_ecb_decrypt(const QByteArray& ciphertext_b64, const QByteArray& key);

// RSA encrypt data với PEM public key → base64 ciphertext.
QByteArray rsa_encrypt(const QByteArray& data, const QString& pem_key);

// Encode RSA-encrypted AES key theo format upstream: reverseChunks + base64.
QString encode_string(const QString& input);

// ── High-level API ──

struct EncryptResult {
    QByteArray encrypted_body;   // base64 AES ciphertext
    QString cek_k;               // header value cho "cek-k"
    QByteArray aes_key;          // để decrypt response
    bool ok = false;
    QString error;
};

// Encrypt request body (JSON string) với encrypt_public_key.
EncryptResult encrypt_request(const QByteArray& json_body, const QString& encrypt_public_key);

// Encrypt với decoded PEM key (đã cache) — skip decode step.
EncryptResult encrypt_request_with_pem(const QByteArray& json_body, const QString& decoded_pem);

// Decrypt response body khi cek-s=1.
QByteArray decrypt_response(const QByteArray& body_b64, const QByteArray& aes_key);

} // namespace UpstreamCrypto
