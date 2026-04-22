package shortener

import (
	"testing"
)

func TestGenerateShortCode(t *testing.T) {
	code, err := GenerateShortCode(7)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(code) != 7 {
		t.Errorf("Expected length 7, got %d", len(code))
	}
}

func TestValidateURL(t *testing.T) {
	tests := []struct {
		url      string
		expected bool
	}{
		{"https://google.com", true},
		{"http://example.com/path", true},
		{"ftp://invalid.com", false},
		{"not-a-url", false},
	}

	for _, tt := range tests {
		result := ValidateURL(tt.url)
		if result != tt.expected {
			t.Errorf("ValidateURL(%q) = %v; expected %v", tt.url, result, tt.expected)
		}
	}
}
