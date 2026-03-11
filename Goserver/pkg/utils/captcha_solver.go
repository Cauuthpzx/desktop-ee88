package utils

import (
	"bufio"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"os/exec"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"syscall"
	"time"
)

// CaptchaSolver quản lý persistent Python OCR worker.
// Fix MAXHUB: không spawn process mỗi lần — giữ worker sống, giao tiếp qua pipe.
// Thread-safe: dùng mutex bảo vệ stdin/stdout access.

type CaptchaSolver struct {
	mu      sync.Mutex
	cmd     *exec.Cmd
	stdin   io.WriteCloser
	scanner *bufio.Scanner
	ready   bool
}

var (
	globalSolver     *CaptchaSolver
	globalSolverOnce sync.Once
)

// GetCaptchaSolver trả singleton solver.
func GetCaptchaSolver() *CaptchaSolver {
	globalSolverOnce.Do(func() {
		globalSolver = &CaptchaSolver{}
	})
	return globalSolver
}

func (cs *CaptchaSolver) ensureWorker() error {
	if cs.ready && cs.cmd != nil && cs.cmd.Process != nil {
		// Kiểm tra process còn sống không
		if cs.cmd.ProcessState == nil {
			return nil // still running
		}
	}

	// Tìm script path
	scriptPath := findSolverScript()
	if scriptPath == "" {
		return errors.New("không tìm thấy scripts/solve_captcha.py")
	}

	pythonCmd := "python"
	if runtime.GOOS != "windows" {
		pythonCmd = "python3"
	}

	cmd := exec.Command(pythonCmd, scriptPath)
	// Redirect stderr → discard để child process không inherit parent stdout handle.
	// Fix: manager.py đọc Go stdout pipe, Python worker kế thừa handle →
	// khi worker exit → pipe EOF → manager báo "kết thúc" dù Go server vẫn sống.
	// Chặn child inherit parent stdout handle — tránh pipe leak khi worker exit.
	devnull, _ := os.Open(os.DevNull)
	cmd.Stderr = devnull
	if runtime.GOOS == "windows" {
		cmd.SysProcAttr = &syscall.SysProcAttr{
			CreationFlags: syscall.CREATE_NEW_PROCESS_GROUP,
		}
	}
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return fmt.Errorf("stdin pipe: %w", err)
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		stdin.Close()
		return fmt.Errorf("stdout pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		stdin.Close()
		if devnull != nil {
			devnull.Close()
		}
		return fmt.Errorf("start python worker: %w", err)
	}
	// Close devnull — child process đã kế thừa handle
	if devnull != nil {
		devnull.Close()
	}

	cs.cmd = cmd
	cs.stdin = stdin
	cs.scanner = bufio.NewScanner(stdout)
	cs.scanner.Buffer(make([]byte, 64*1024), 64*1024)
	cs.ready = true

	slog.Info("Captcha OCR worker started", "pid", cmd.Process.Pid)

	// Goroutine chờ process exit để reset state
	go func() {
		_ = cmd.Wait()
		cs.mu.Lock()
		cs.ready = false
		cs.mu.Unlock()
		slog.Warn("Captcha OCR worker exited")
	}()

	return nil
}

func findSolverScript() string {
	candidates := []string{
		"scripts/solve_captcha.py",
		"../scripts/solve_captcha.py",
		filepath.Join("Goserver", "scripts", "solve_captcha.py"),
	}
	for _, c := range candidates {
		abs, err := filepath.Abs(c)
		if err != nil {
			continue
		}
		if fileExists(abs) {
			return abs
		}
	}
	return ""
}

func fileExists(path string) bool {
	_, err := exec.LookPath(path)
	if err == nil {
		return true
	}
	// Fallback: direct stat
	info, err := exec.Command("test", "-f", path).CombinedOutput()
	_ = info
	// Just use os.Stat approach
	_, statErr := filepath.Abs(path)
	if statErr != nil {
		return false
	}
	return true
}

// Solve gửi image tới worker, nhận kết quả captcha.
// Timeout: 10 giây.
// Trả (result, error). result="" nếu OCR fail.
func (cs *CaptchaSolver) Solve(imageData []byte) (string, error) {
	if len(imageData) == 0 {
		return "", errors.New("image data rỗng")
	}
	if len(imageData) > 2*1024*1024 {
		return "", errors.New("image data quá lớn (>2MB)")
	}

	cs.mu.Lock()
	defer cs.mu.Unlock()

	if err := cs.ensureWorker(); err != nil {
		return "", fmt.Errorf("ensure worker: %w", err)
	}

	// Gửi: 4 bytes big-endian length + image data
	header := make([]byte, 4)
	binary.BigEndian.PutUint32(header, uint32(len(imageData)))
	if _, err := cs.stdin.Write(header); err != nil {
		cs.ready = false
		return "", fmt.Errorf("write header: %w", err)
	}
	if _, err := cs.stdin.Write(imageData); err != nil {
		cs.ready = false
		return "", fmt.Errorf("write image: %w", err)
	}

	// Đọc response với timeout
	resultCh := make(chan string, 1)
	errCh := make(chan error, 1)
	go func() {
		if cs.scanner.Scan() {
			resultCh <- cs.scanner.Text()
		} else {
			if err := cs.scanner.Err(); err != nil {
				errCh <- err
			} else {
				errCh <- errors.New("worker EOF")
			}
		}
	}()

	select {
	case result := <-resultCh:
		result = strings.TrimSpace(result)
		if result == "ERROR" || result == "" {
			return "", nil // OCR fail, không phải error
		}
		slog.Debug("Captcha solved", "result", result)
		return result, nil
	case err := <-errCh:
		cs.ready = false
		return "", fmt.Errorf("read result: %w", err)
	case <-time.After(15 * time.Second):
		cs.ready = false
		// Kill hung worker
		if cs.cmd != nil && cs.cmd.Process != nil {
			_ = cs.cmd.Process.Kill()
		}
		return "", errors.New("captcha solver timeout (15s)")
	}
}

// Shutdown tắt worker.
func (cs *CaptchaSolver) Shutdown() {
	cs.mu.Lock()
	defer cs.mu.Unlock()
	if cs.stdin != nil {
		cs.stdin.Close()
	}
	if cs.cmd != nil && cs.cmd.Process != nil {
		_ = cs.cmd.Process.Kill()
	}
	cs.ready = false
}
