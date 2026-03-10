module goserver

go 1.24.0

require (
	github.com/golang-jwt/jwt/v5 v5.2.1
	github.com/jmoiron/sqlx v1.4.0
	github.com/jordan-wright/email v4.0.1-0.20210109023952-943e75fe5223+incompatible
	github.com/lib/pq v1.10.9
	golang.org/x/crypto v0.33.0
	golang.org/x/oauth2 v0.34.0
)

require cloud.google.com/go/compute/metadata v0.3.0 // indirect
