package service

import (
	"context"
	"errors"
	"time"
	"unicode"

	"github.com/golang-jwt/jwt/v5"

	"goserver/internal/config"
	"goserver/internal/model"
	"goserver/internal/repository"
	"goserver/pkg/utils"
)

var (
	ErrInvalidUsername   = errors.New("username must be 3-32 characters, alphanumeric and underscore only")
	ErrPasswordTooShort = errors.New("password must be at least 8 characters")
	ErrInvalidCredentials = errors.New("invalid username or password")
	ErrSamePassword    = errors.New("new password must be different from old password")
	ErrWrongOldPassword = errors.New("old password is incorrect")
)

type AuthService struct {
	repo *repository.UserRepository
	cfg  *config.Config
}

func NewAuthService(repo *repository.UserRepository, cfg *config.Config) *AuthService {
	return &AuthService{repo: repo, cfg: cfg}
}

func (s *AuthService) Register(ctx context.Context, req *model.RegisterRequest) (*model.User, string, error) {
	if err := validateUsername(req.Username); err != nil {
		return nil, "", err
	}
	if len(req.Password) < 8 {
		return nil, "", ErrPasswordTooShort
	}

	hashedPassword, err := utils.HashPassword(req.Password)
	if err != nil {
		return nil, "", err
	}

	user, err := s.repo.Create(ctx, req.Username, hashedPassword)
	if err != nil {
		return nil, "", err
	}

	token, err := s.generateJWT(user)
	if err != nil {
		return nil, "", err
	}

	return user, token, nil
}

func (s *AuthService) Login(ctx context.Context, req *model.LoginRequest) (*model.User, string, string, error) {
	user, err := s.repo.FindByUsername(ctx, req.Username)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			return nil, "", "", ErrInvalidCredentials
		}
		return nil, "", "", err
	}

	if !utils.CheckPassword(user.Password, req.Password) {
		return nil, "", "", ErrInvalidCredentials
	}

	_ = s.repo.UpdateLastSeen(ctx, user.ID)

	token, err := s.generateJWT(user)
	if err != nil {
		return nil, "", "", err
	}

	sessionCookie, err := utils.GenerateToken(32)
	if err != nil {
		return nil, "", "", err
	}

	if err := s.repo.CreateSession(ctx, sessionCookie, user.ID); err != nil {
		return nil, "", "", err
	}

	return user, token, sessionCookie, nil
}

func (s *AuthService) ChangePassword(ctx context.Context, userID int64, req *model.ChangePasswordRequest) error {
	if len(req.NewPassword) < 8 {
		return ErrPasswordTooShort
	}
	if req.OldPassword == req.NewPassword {
		return ErrSamePassword
	}

	user, err := s.repo.FindByID(ctx, userID)
	if err != nil {
		return err
	}

	if !utils.CheckPassword(user.Password, req.OldPassword) {
		return ErrWrongOldPassword
	}

	hashedPassword, err := utils.HashPassword(req.NewPassword)
	if err != nil {
		return err
	}

	if err := s.repo.UpdatePassword(ctx, userID, hashedPassword); err != nil {
		return err
	}

	_ = s.repo.DeleteUserSessions(ctx, userID)

	return nil
}

func (s *AuthService) Logout(ctx context.Context, sessionCookie string) error {
	return s.repo.DeleteSession(ctx, sessionCookie)
}

func (s *AuthService) ValidateJWT(tokenString string) (int64, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return []byte(s.cfg.JWTSecret), nil
	})
	if err != nil {
		return 0, err
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok || !token.Valid {
		return 0, errors.New("invalid token")
	}

	userID, ok := claims["user_id"].(float64)
	if !ok {
		return 0, errors.New("invalid token claims")
	}

	return int64(userID), nil
}

func (s *AuthService) FindUserBySession(ctx context.Context, cookie string) (*model.User, error) {
	session, err := s.repo.FindSession(ctx, cookie)
	if err != nil {
		return nil, err
	}
	if session == nil {
		return nil, nil
	}
	return s.repo.FindByID(ctx, session.UserID)
}

func (s *AuthService) FindUserByID(ctx context.Context, id int64) (*model.User, error) {
	return s.repo.FindByID(ctx, id)
}

func (s *AuthService) generateJWT(user *model.User) (string, error) {
	claims := jwt.MapClaims{
		"user_id":  user.ID,
		"username": user.Username,
		"exp":      time.Now().Add(s.cfg.JWTExpiry).Unix(),
		"iat":      time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(s.cfg.JWTSecret))
}

func validateUsername(username string) error {
	if len(username) < 3 || len(username) > 32 {
		return ErrInvalidUsername
	}
	for _, r := range username {
		if !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_' {
			return ErrInvalidUsername
		}
	}
	return nil
}
