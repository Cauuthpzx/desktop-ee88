package utils

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"errors"
	"fmt"
)

// ============================================================================
// RSA encryption — dùng cho mã hóa password gửi lên EE88.
// ============================================================================

func EncryptRSA(plaintext, publicKeyPEM string) (string, error) {
	// Thử parse PKCS8 trước, nếu fail thì thử PKCS1
	block, _ := pem.Decode([]byte(publicKeyPEM))
	if block == nil {
		// Nếu key không có PEM header, wrap lại
		wrapped := "-----BEGIN PUBLIC KEY-----\n" + publicKeyPEM + "\n-----END PUBLIC KEY-----"
		block, _ = pem.Decode([]byte(wrapped))
		if block == nil {
			return "", errors.New("không thể parse RSA public key PEM")
		}
	}

	pub, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		// Fallback: thử PKCS1
		rsaPub, err2 := x509.ParsePKCS1PublicKey(block.Bytes)
		if err2 != nil {
			return "", fmt.Errorf("parse public key failed: PKIX=%v, PKCS1=%v", err, err2)
		}
		pub = rsaPub
	}

	rsaKey, ok := pub.(*rsa.PublicKey)
	if !ok {
		return "", errors.New("public key không phải RSA")
	}

	encrypted, err := rsa.EncryptPKCS1v15(rand.Reader, rsaKey, []byte(plaintext))
	if err != nil {
		return "", fmt.Errorf("rsa.EncryptPKCS1v15: %w", err)
	}

	return base64.StdEncoding.EncodeToString(encrypted), nil
}
