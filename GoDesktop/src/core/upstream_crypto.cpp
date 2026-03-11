#include "core/upstream_crypto.h"

#include <QRandomGenerator>
#include <QStringList>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/pem.h>

#include <cstring>
#include <memory>

namespace UpstreamCrypto {

// ── RAII wrappers for OpenSSL resources ──

struct EvpCipherCtxDeleter {
    void operator()(EVP_CIPHER_CTX* ctx) const { EVP_CIPHER_CTX_free(ctx); }
};
using EvpCipherCtxPtr = std::unique_ptr<EVP_CIPHER_CTX, EvpCipherCtxDeleter>;

struct EvpPkeyDeleter {
    void operator()(EVP_PKEY* pkey) const { EVP_PKEY_free(pkey); }
};
using EvpPkeyPtr = std::unique_ptr<EVP_PKEY, EvpPkeyDeleter>;

struct EvpPkeyCtxDeleter {
    void operator()(EVP_PKEY_CTX* ctx) const { EVP_PKEY_CTX_free(ctx); }
};
using EvpPkeyCtxPtr = std::unique_ptr<EVP_PKEY_CTX, EvpPkeyCtxDeleter>;

struct BioDeleter {
    void operator()(BIO* bio) const { BIO_free(bio); }
};
using BioPtr = std::unique_ptr<BIO, BioDeleter>;

// ── reverseChunks ──

QString reverse_chunks(const QString& input)
{
    QString result;
    result.reserve(input.size());
    int pos = 0;
    int cs = 2;
    while (pos < input.size()) {
        int end = qMin(pos + cs, input.size());
        QString chunk = input.mid(pos, end - pos);
        std::reverse(chunk.begin(), chunk.end());
        result.append(chunk);
        pos = end;
        ++cs;
        if (cs > 8) cs = 2;
    }
    return result;
}

// ── Decode encrypt_public_key ──

QString decode_encrypt_public_key(const QString& encoded_key)
{
    QByteArray decoded = QByteArray::fromBase64(encoded_key.toUtf8());
    QString key_base64 = reverse_chunks(QString::fromUtf8(decoded));

    if (!key_base64.contains("BEGIN")) {
        QStringList lines;
        for (int i = 0; i < key_base64.size(); i += 64) {
            lines.append(key_base64.mid(i, 64));
        }
        key_base64 = "-----BEGIN PUBLIC KEY-----\n"
                     + lines.join("\n")
                     + "\n-----END PUBLIC KEY-----";
    }

    return key_base64;
}

// ── Generate AES key ──

QByteArray generate_aes_key()
{
    static const char charset[] =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    constexpr int charset_len = sizeof(charset) - 1;

    QByteArray key(16, '\0');
    auto* rng = QRandomGenerator::global();
    for (int i = 0; i < 16; ++i) {
        key[i] = charset[rng->bounded(charset_len)];
    }
    return key;
}

// ── AES-ECB encrypt (EVP API + RAII) ──

QByteArray aes_ecb_encrypt(const QByteArray& plaintext, const QByteArray& key)
{
    if (key.size() != 16) return {};

    EvpCipherCtxPtr ctx(EVP_CIPHER_CTX_new());
    if (!ctx) return {};

    if (EVP_EncryptInit_ex(ctx.get(), EVP_aes_128_ecb(), nullptr,
            reinterpret_cast<const unsigned char*>(key.constData()), nullptr) != 1) {
        return {};
    }

    QByteArray result(plaintext.size() + 16, '\0');
    int out_len = 0;
    if (EVP_EncryptUpdate(ctx.get(), reinterpret_cast<unsigned char*>(result.data()), &out_len,
                          reinterpret_cast<const unsigned char*>(plaintext.constData()),
                          plaintext.size()) != 1) {
        return {};
    }

    int final_len = 0;
    if (EVP_EncryptFinal_ex(ctx.get(), reinterpret_cast<unsigned char*>(result.data()) + out_len,
                             &final_len) != 1) {
        return {};
    }

    result.resize(out_len + final_len);
    return result.toBase64();
}

// ── AES-ECB decrypt (EVP API + RAII) ──

QByteArray aes_ecb_decrypt(const QByteArray& ciphertext_b64, const QByteArray& key)
{
    if (key.size() != 16) return {};

    QByteArray ct = QByteArray::fromBase64(ciphertext_b64);
    if (ct.isEmpty() || ct.size() % 16 != 0) return {};

    EvpCipherCtxPtr ctx(EVP_CIPHER_CTX_new());
    if (!ctx) return {};

    if (EVP_DecryptInit_ex(ctx.get(), EVP_aes_128_ecb(), nullptr,
            reinterpret_cast<const unsigned char*>(key.constData()), nullptr) != 1) {
        return {};
    }

    QByteArray result(ct.size() + 16, '\0');
    int out_len = 0;
    if (EVP_DecryptUpdate(ctx.get(), reinterpret_cast<unsigned char*>(result.data()), &out_len,
                          reinterpret_cast<const unsigned char*>(ct.constData()),
                          ct.size()) != 1) {
        return {};
    }

    int final_len = 0;
    if (EVP_DecryptFinal_ex(ctx.get(), reinterpret_cast<unsigned char*>(result.data()) + out_len,
                             &final_len) != 1) {
        return {};
    }

    result.resize(out_len + final_len);
    return result;
}

// ── RSA encrypt (RAII) ──

QByteArray rsa_encrypt(const QByteArray& data, const QString& pem_key)
{
    QByteArray pem_bytes = pem_key.toUtf8();
    BioPtr bio(BIO_new_mem_buf(pem_bytes.constData(), pem_bytes.size()));
    if (!bio) return {};

    EvpPkeyPtr pkey(PEM_read_bio_PUBKEY(bio.get(), nullptr, nullptr, nullptr));
    if (!pkey) return {};

    EvpPkeyCtxPtr ctx(EVP_PKEY_CTX_new(pkey.get(), nullptr));
    if (!ctx) return {};

    if (EVP_PKEY_encrypt_init(ctx.get()) <= 0
        || EVP_PKEY_CTX_set_rsa_padding(ctx.get(), RSA_PKCS1_PADDING) <= 0) {
        return {};
    }

    size_t out_len = 0;
    if (EVP_PKEY_encrypt(ctx.get(), nullptr, &out_len,
                         reinterpret_cast<const unsigned char*>(data.constData()),
                         static_cast<size_t>(data.size())) <= 0) {
        return {};
    }

    QByteArray result(static_cast<int>(out_len), '\0');
    if (EVP_PKEY_encrypt(ctx.get(), reinterpret_cast<unsigned char*>(result.data()), &out_len,
                         reinterpret_cast<const unsigned char*>(data.constData()),
                         static_cast<size_t>(data.size())) <= 0) {
        return {};
    }

    result.resize(static_cast<int>(out_len));
    return result;
}

// ── encodeString ──

QString encode_string(const QString& input)
{
    QString reversed = reverse_chunks(input);
    return QString::fromUtf8(reversed.toUtf8().toBase64());
}

// ── High-level: encrypt request ──

EncryptResult encrypt_request(const QByteArray& json_body, const QString& encrypt_public_key)
{
    EncryptResult r;

    QString pem = decode_encrypt_public_key(encrypt_public_key);
    if (pem.isEmpty()) {
        r.error = "decode encrypt_public_key failed";
        return r;
    }

    r.aes_key = generate_aes_key();

    r.encrypted_body = aes_ecb_encrypt(json_body, r.aes_key);
    if (r.encrypted_body.isEmpty()) {
        r.error = "AES-ECB encrypt failed";
        return r;
    }

    QByteArray rsa_encrypted = rsa_encrypt(r.aes_key, pem);
    if (rsa_encrypted.isEmpty()) {
        r.error = "RSA encrypt AES key failed";
        return r;
    }
    QString rsa_b64 = QString::fromUtf8(rsa_encrypted.toBase64());

    r.cek_k = encode_string(rsa_b64);
    r.ok = true;
    return r;
}

// ── High-level: encrypt with pre-decoded PEM (skip decode step) ──

EncryptResult encrypt_request_with_pem(const QByteArray& json_body, const QString& decoded_pem)
{
    EncryptResult r;

    if (decoded_pem.isEmpty()) {
        r.error = "empty decoded PEM key";
        return r;
    }

    r.aes_key = generate_aes_key();

    r.encrypted_body = aes_ecb_encrypt(json_body, r.aes_key);
    if (r.encrypted_body.isEmpty()) {
        r.error = "AES-ECB encrypt failed";
        return r;
    }

    QByteArray rsa_encrypted = rsa_encrypt(r.aes_key, decoded_pem);
    if (rsa_encrypted.isEmpty()) {
        r.error = "RSA encrypt AES key failed";
        return r;
    }
    QString rsa_b64 = QString::fromUtf8(rsa_encrypted.toBase64());

    r.cek_k = encode_string(rsa_b64);
    r.ok = true;
    return r;
}

// ── High-level: decrypt response ──

QByteArray decrypt_response(const QByteArray& body_b64, const QByteArray& aes_key)
{
    return aes_ecb_decrypt(body_b64, aes_key);
}

} // namespace UpstreamCrypto
