//go:build !windows

package utils

import "os/exec"

func setSysProcAttr(_ *exec.Cmd) {
	// No special process attributes needed on Unix
}
