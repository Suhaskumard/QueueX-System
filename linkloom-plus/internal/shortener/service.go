package shortener

import (
	"crypto/rand"
	"math/big"
	neturl "net/url"
)

const base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

func GenerateShortCode(length int) (string, error) {
	bytes := make([]byte, length)
	for i := 0; i < length; i++ {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(base58Alphabet))))
		if err != nil {
			return "", err
		}
		bytes[i] = base58Alphabet[num.Int64()]
	}
	return string(bytes), nil
}

func ValidateURL(rawURL string) bool {
	u, err := neturl.ParseRequestURI(rawURL)
	if err != nil {
		return false
	}
	return u.Scheme == "http" || u.Scheme == "https"
}
