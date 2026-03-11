package utils

import (
	"crypto/aes"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"fmt"
	"math/big"
	mrand "math/rand"
	"strings"
	"time"
)

// ============================================================================
// AgentEncrypt — AES-ECB encrypt mode cho EE88 upstream.
// Port từ agent-encrypt.js (obfuscated).
//
// Flow:
//  1. Init: decode encrypt_public_key (reverseChunks) → RSA PEM
//  2. Generate random 16-char AES key
//  3. AES-ECB encrypt JSON body (PKCS7 padding)
//  4. RSA encrypt AES key → encodeString (reverseChunks) → header cek-k
//  5. Send: Content-Type text/plain, body = AES ciphertext (base64)
// ============================================================================

// reverseChunks xử lý encode/decode theo cách upstream obfuscate key.
// Chunk sizes cycle: 2, 3, 4, 5, 6, 7, 8, 2, 3, ...
// Hàm tự inverse: reverseChunks(reverseChunks(x)) == x
func reverseChunks(s string) string {
	runes := []rune(s)
	var result []rune
	pos := 0
	cs := 2
	for pos < len(runes) {
		end := pos + cs
		if end > len(runes) {
			end = len(runes)
		}
		chunk := make([]rune, end-pos)
		copy(chunk, runes[pos:end])
		// reverse chunk
		for i, j := 0, len(chunk)-1; i < j; i, j = i+1, j-1 {
			chunk[i], chunk[j] = chunk[j], chunk[i]
		}
		result = append(result, chunk...)
		pos = end
		cs++
		if cs > 8 {
			cs = 2
		}
	}
	return string(result)
}

// DecodeEncryptPublicKey giải mã encrypt_public_key từ upstream.
// Input: base64 encoded + reverseChunks obfuscated RSA public key.
// Output: PEM formatted RSA public key.
func DecodeEncryptPublicKey(encodedKey string) (string, error) {
	decoded, err := base64.StdEncoding.DecodeString(encodedKey)
	if err != nil {
		return "", fmt.Errorf("base64 decode encrypt_public_key: %w", err)
	}

	keyBase64 := reverseChunks(string(decoded))

	// Wrap thành PEM nếu chưa có header
	if !strings.Contains(keyBase64, "BEGIN") {
		// Split thành lines 64 chars
		var lines []string
		for i := 0; i < len(keyBase64); i += 64 {
			end := i + 64
			if end > len(keyBase64) {
				end = len(keyBase64)
			}
			lines = append(lines, keyBase64[i:end])
		}
		keyBase64 = "-----BEGIN PUBLIC KEY-----\n" + strings.Join(lines, "\n") + "\n-----END PUBLIC KEY-----"
	}

	return keyBase64, nil
}

// generateAESKey tạo random 16-char alphanumeric key.
func generateAESKey() string {
	const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
	r := mrand.New(mrand.NewSource(time.Now().UnixNano()))
	b := make([]byte, 16)
	for i := range b {
		b[i] = charset[r.Intn(len(charset))]
	}
	return string(b)
}

// pkcs7Pad thêm PKCS7 padding cho AES block.
func pkcs7Pad(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	pad := make([]byte, padding)
	for i := range pad {
		pad[i] = byte(padding)
	}
	return append(data, pad...)
}

// aesECBEncrypt mã hóa plaintext bằng AES-ECB + PKCS7 padding.
// Key là UTF-8 string (16 bytes).
// Output: base64 encoded ciphertext.
func aesECBEncrypt(plaintext, key string) (string, error) {
	keyBytes := []byte(key)
	if len(keyBytes) != 16 {
		return "", fmt.Errorf("AES key phải 16 bytes, got %d", len(keyBytes))
	}

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return "", fmt.Errorf("aes.NewCipher: %w", err)
	}

	padded := pkcs7Pad([]byte(plaintext), aes.BlockSize)
	encrypted := make([]byte, len(padded))

	// ECB mode: encrypt từng block riêng
	for i := 0; i < len(padded); i += aes.BlockSize {
		block.Encrypt(encrypted[i:i+aes.BlockSize], padded[i:i+aes.BlockSize])
	}

	return base64.StdEncoding.EncodeToString(encrypted), nil
}

// encodeString mã hóa RSA-encrypted AES key theo format upstream.
// reverseChunks + base64 encode.
func encodeString(s string) string {
	reversed := reverseChunks(s)
	return base64.StdEncoding.EncodeToString([]byte(reversed))
}

// AgentEncryptData mã hóa request data theo AES mode của EE88 upstream.
// Input: jsonBody = JSON string, encryptPublicKey = encrypt_public_key từ init.
// Output: encryptedBody (AES ciphertext), cekK (header value), usedAESKey (để decrypt response), error.
func AgentEncryptData(jsonBody, encryptPublicKey string) (encryptedBody, cekK, usedAESKey string, err error) {
	// 1. Decode encrypt_public_key → RSA PEM
	rsaPEM, err := DecodeEncryptPublicKey(encryptPublicKey)
	if err != nil {
		return "", "", "", fmt.Errorf("decode encrypt public key: %w", err)
	}

	// 2. Parse RSA public key
	pemBlock, _ := pem.Decode([]byte(rsaPEM))
	if pemBlock == nil {
		return "", "", "", fmt.Errorf("pem.Decode failed for encrypt_public_key")
	}

	pub, err := x509.ParsePKIXPublicKey(pemBlock.Bytes)
	if err != nil {
		// Fallback PKCS1
		rsaPub, err2 := x509.ParsePKCS1PublicKey(pemBlock.Bytes)
		if err2 != nil {
			return "", "", "", fmt.Errorf("parse encrypt public key: PKIX=%v, PKCS1=%v", err, err2)
		}
		pub = rsaPub
	}

	rsaKey, ok := pub.(*rsa.PublicKey)
	if !ok {
		return "", "", "", fmt.Errorf("encrypt public key không phải RSA")
	}

	// 3. Generate random AES key (16 chars)
	aesKey := generateAESKey()

	// 4. AES-ECB encrypt body
	encryptedBody, err = aesECBEncrypt(jsonBody, aesKey)
	if err != nil {
		return "", "", "", fmt.Errorf("AES-ECB encrypt: %w", err)
	}

	// 5. RSA encrypt AES key
	rsaEncrypted, err := rsa.EncryptPKCS1v15(rand.Reader, rsaKey, []byte(aesKey))
	if err != nil {
		return "", "", "", fmt.Errorf("RSA encrypt AES key: %w", err)
	}
	rsaEncryptedB64 := base64.StdEncoding.EncodeToString(rsaEncrypted)

	// 6. Encode RSA-encrypted AES key (reverseChunks + base64)
	cekK = encodeString(rsaEncryptedB64)

	return encryptedBody, cekK, aesKey, nil
}

// AgentDecryptResponse giải mã response từ upstream khi cek-s=1.
func AgentDecryptResponse(ciphertext, aesKey string) (string, error) {
	keyBytes := []byte(aesKey)
	if len(keyBytes) != 16 {
		return "", fmt.Errorf("AES key phải 16 bytes")
	}

	ct, err := base64.StdEncoding.DecodeString(ciphertext)
	if err != nil {
		return "", fmt.Errorf("base64 decode: %w", err)
	}

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return "", err
	}

	if len(ct)%aes.BlockSize != 0 {
		return "", fmt.Errorf("ciphertext length not multiple of block size")
	}

	decrypted := make([]byte, len(ct))
	for i := 0; i < len(ct); i += aes.BlockSize {
		block.Decrypt(decrypted[i:i+aes.BlockSize], ct[i:i+aes.BlockSize])
	}

	// Remove PKCS7 padding
	if len(decrypted) > 0 {
		padLen := int(decrypted[len(decrypted)-1])
		if padLen > 0 && padLen <= aes.BlockSize && padLen <= len(decrypted) {
			decrypted = decrypted[:len(decrypted)-padLen]
		}
	}

	return string(decrypted), nil
}

// rsaKeyBitSize lấy bit size của RSA key — helper cho debug.
func rsaKeyBitSize(key *rsa.PublicKey) int {
	return key.N.BitLen()
}

// init seed random
func init() {
	_ = big.NewInt(0) // ensure math/big is imported for RSA
}
