package service

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"golang.org/x/oauth2"
	"golang.org/x/oauth2/facebook"
	"golang.org/x/oauth2/google"

	"goserver/internal/config"
	"goserver/internal/model"
	"goserver/internal/repository"
	"goserver/pkg/utils"
)

type OAuthService struct {
	repo           repository.UserRepo
	authService    *AuthService
	googleConfig   *oauth2.Config
	facebookConfig *oauth2.Config
	cfg            *config.Config
}

func NewOAuthService(repo repository.UserRepo, authService *AuthService, cfg *config.Config) *OAuthService {
	return &OAuthService{
		repo:        repo,
		authService: authService,
		cfg:         cfg,
		googleConfig: &oauth2.Config{
			ClientID:     cfg.GoogleClientID,
			ClientSecret: cfg.GoogleClientSecret,
			RedirectURL:  cfg.GoogleRedirectURL,
			Scopes:       []string{"openid", "email", "profile"},
			Endpoint:     google.Endpoint,
		},
		facebookConfig: &oauth2.Config{
			ClientID:     cfg.FacebookClientID,
			ClientSecret: cfg.FacebookClientSecret,
			RedirectURL:  cfg.FacebookRedirectURL,
			Scopes:       []string{"email"},
			Endpoint:     facebook.Endpoint,
		},
	}
}

type oauthUserInfo struct {
	ID    string `json:"id"`
	Email string `json:"email"`
}

func (s *OAuthService) GoogleAuthURL(state string) string {
	return s.googleConfig.AuthCodeURL(state)
}

func (s *OAuthService) FacebookAuthURL(state string) string {
	return s.facebookConfig.AuthCodeURL(state)
}

func (s *OAuthService) HandleGoogleCallback(ctx context.Context, code string) (*model.User, string, error) {
	token, err := s.googleConfig.Exchange(ctx, code)
	if err != nil {
		return nil, "", fmt.Errorf("google token exchange failed: %w", err)
	}

	userInfo, err := s.getGoogleUserInfo(ctx, token)
	if err != nil {
		return nil, "", err
	}

	return s.findOrCreateOAuthUser(ctx, "google", userInfo.ID, userInfo.Email, token.AccessToken)
}

func (s *OAuthService) HandleFacebookCallback(ctx context.Context, code string) (*model.User, string, error) {
	token, err := s.facebookConfig.Exchange(ctx, code)
	if err != nil {
		return nil, "", fmt.Errorf("facebook token exchange failed: %w", err)
	}

	userInfo, err := s.getFacebookUserInfo(ctx, token)
	if err != nil {
		return nil, "", err
	}

	return s.findOrCreateOAuthUser(ctx, "facebook", userInfo.ID, userInfo.Email, token.AccessToken)
}

func (s *OAuthService) findOrCreateOAuthUser(ctx context.Context, method, foreignID, email, accessToken string) (*model.User, string, error) {
	existing, err := s.repo.FindOAuth(ctx, method, foreignID)
	if err != nil {
		return nil, "", err
	}

	var user *model.User

	if existing != nil {
		user, err = s.repo.FindByID(ctx, existing.UserID)
		if err != nil {
			return nil, "", err
		}
	} else {
		user, err = s.repo.FindByUsername(ctx, email)
		if err != nil && err != repository.ErrUserNotFound {
			return nil, "", err
		}

		if user == nil {
			user, err = s.repo.Create(ctx, email, "")
			if err != nil {
				return nil, "", err
			}
		}

		oauthEntry := &model.OAuth{
			Method:    method,
			ForeignID: foreignID,
			Token:     accessToken,
			UserID:    user.ID,
		}
		if err := s.repo.CreateOAuth(ctx, oauthEntry); err != nil {
			return nil, "", err
		}
	}

	jwtToken, err := s.authService.generateJWT(user)
	if err != nil {
		return nil, "", err
	}

	return user, jwtToken, nil
}

func (s *OAuthService) getGoogleUserInfo(ctx context.Context, token *oauth2.Token) (*oauthUserInfo, error) {
	client := s.googleConfig.Client(ctx, token)
	resp, err := client.Get("https://www.googleapis.com/oauth2/v2/userinfo")
	if err != nil {
		return nil, fmt.Errorf("failed to get google user info: %w", err)
	}
	defer resp.Body.Close()

	return parseUserInfo(resp)
}

func (s *OAuthService) getFacebookUserInfo(ctx context.Context, token *oauth2.Token) (*oauthUserInfo, error) {
	client := s.facebookConfig.Client(ctx, token)
	resp, err := client.Get("https://graph.facebook.com/me?fields=id,email")
	if err != nil {
		return nil, fmt.Errorf("failed to get facebook user info: %w", err)
	}
	defer resp.Body.Close()

	return parseUserInfo(resp)
}

func parseUserInfo(resp *http.Response) (*oauthUserInfo, error) {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var info oauthUserInfo
	if err := json.Unmarshal(body, &info); err != nil {
		return nil, err
	}

	if info.Email == "" && info.ID != "" {
		info.Email = fmt.Sprintf("%s@oauth.noemail", info.ID)
	}

	if info.Email == "" {
		return nil, fmt.Errorf("email not provided by oauth provider")
	}

	return &info, nil
}

// GenerateState tạo state token cho OAuth CSRF protection
func GenerateState() (string, error) {
	return utils.GenerateToken(16)
}
