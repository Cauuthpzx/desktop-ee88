package service

import (
	"fmt"
	"log"
	"net/smtp"
	"net/textproto"
	"strings"

	"github.com/jordan-wright/email"

	"goserver/internal/config"
)

type EmailConfig struct {
	SMTPServer  string
	SMTPUser    string
	SMTPPassword string
	EmailFrom   string
}

type EmailService struct {
	cfg *config.Config
	smtp EmailConfig
}

func NewEmailService(cfg *config.Config, smtpCfg EmailConfig) *EmailService {
	return &EmailService{cfg: cfg, smtp: smtpCfg}
}

func (s *EmailService) SendPasswordReset(toAddr, token string) error {
	resetURL := fmt.Sprintf("%s/auth/reset-password?token=%s", s.cfg.FrontendURL, token)

	e := &email.Email{
		To:      []string{toAddr},
		From:    s.smtp.EmailFrom,
		Subject: "Password Reset Request",
		Text:    []byte(fmt.Sprintf("Click the link to reset your password: %s", resetURL)),
		Headers: textproto.MIMEHeader{},
	}

	host := strings.Split(s.smtp.SMTPServer, ":")[0]
	auth := smtp.PlainAuth("", s.smtp.SMTPUser, s.smtp.SMTPPassword, host)

	if err := e.Send(s.smtp.SMTPServer, auth); err != nil {
		log.Printf("Error sending password reset email to %s: %v", toAddr, err)
		return fmt.Errorf("failed to send email: %w", err)
	}

	log.Printf("Password reset email sent to %s", toAddr)
	return nil
}
