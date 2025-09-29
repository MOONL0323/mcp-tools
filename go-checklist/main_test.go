package main

import (
	"mcp-checklist-checker/internal/checker"
	"mcp-checklist-checker/internal/checklist"
	"mcp-checklist-checker/internal/config"
	"os"
	"path/filepath"
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

// TestConfigLoad 测试配置加载
func TestConfigLoad(t *testing.T) {
	Convey("配置加载测试", t, func() {
		Convey("加载默认配置", func() {
			cfg, err := config.LoadConfig()

			So(err, ShouldBeNil)
			So(cfg, ShouldNotBeNil)

			Convey("验证默认配置值", func() {
				So(cfg.DefaultChecklist, ShouldEqual, "go-basic")
			})
		})
	})
}

// TestChecklistLoad 测试检查清单加载
func TestChecklistLoad(t *testing.T) {
	Convey("检查清单加载测试", t, func() {
		Convey("加载 JSON 格式检查清单", func() {
			cl, err := checklist.LoadChecklist("checklists/go-basic.json")

			So(err, ShouldBeNil)
			So(cl, ShouldNotBeNil)

			Convey("验证检查清单内容", func() {
				So(cl.Name, ShouldNotBeEmpty)
				So(len(cl.Items), ShouldBeGreaterThan, 0)
			})

			Convey("验证检查清单格式", func() {
				err := cl.ValidateChecklist()
				So(err, ShouldBeNil)
			})
		})
	})
}

// TestChecklistValidation 测试检查清单验证
func TestChecklistValidation(t *testing.T) {
	Convey("检查清单验证测试", t, func() {
		Convey("验证有效的检查清单", func() {
			cl := &checklist.Checklist{
				Name:    "Test Checklist",
				Version: "1.0.0",
				Items: []checklist.ChecklistItem{
					{
						ID:       "test-item",
						Name:     "Test Item",
						Severity: "warning",
					},
				},
			}

			err := cl.ValidateChecklist()
			So(err, ShouldBeNil)
		})

		Convey("验证无效的检查清单", func() {
			invalidCl := &checklist.Checklist{
				Name:  "",
				Items: []checklist.ChecklistItem{},
			}

			err := invalidCl.ValidateChecklist()
			So(err, ShouldNotBeNil)
		})
	})
}

// TestCodeChecker 测试代码检查器
func TestCodeChecker(t *testing.T) {
	Convey("代码检查器测试", t, func() {
		Convey("创建代码检查器", func() {
			cl, err := checklist.LoadChecklist("checklists/go-basic.json")
			So(err, ShouldBeNil)

			codeChecker := checker.NewCodeChecker(cl)
			So(codeChecker, ShouldNotBeNil)

			Convey("检查文件功能", func() {
				if _, err := os.Stat("test_code.go"); err == nil {
					report, err := codeChecker.CheckFile("test_code.go")

					So(err, ShouldBeNil)
					So(report, ShouldNotBeNil)
					So(report.ChecklistName, ShouldEqual, cl.Name)
				} else {
					// 如果测试文件不存在，跳过此测试
					So(true, ShouldBeTrue)
				}
			})
		})
	})
}

// TestIsCodeFile 测试文件类型判断
func TestIsCodeFile(t *testing.T) {
	Convey("文件类型判断测试", t, func() {
		testCases := []struct {
			ext      string
			expected bool
			desc     string
		}{
			{".go", true, "Go 源文件"},
			{".mod", true, "Go 模块文件"},
			{".sum", true, "Go 校验和文件"},
			{".py", false, "Python 文件"},
			{".js", false, "JavaScript 文件"},
			{".txt", false, "文本文件"},
			{"", false, "无扩展名"},
		}

		for _, tc := range testCases {
			Convey("测试 "+tc.desc, func() {
				result := isCodeFile(tc.ext)
				So(result, ShouldEqual, tc.expected)
			})
		}
	})
}

// TestMCPServerCreation 测试 MCP 服务器创建
func TestMCPServerCreation(t *testing.T) {
	Convey("MCP 服务器创建测试", t, func() {
		Convey("创建 MCP 服务器实例", func() {
			server := NewMCPChecklistServer()

			So(server, ShouldNotBeNil)
			So(server.config, ShouldNotBeNil)
		})
	})
}

// TestTemporaryFileChecking 集成测试
func TestTemporaryFileChecking(t *testing.T) {
	Convey("临时文件检查集成测试", t, func() {
		tempDir := t.TempDir()
		testFile := filepath.Join(tempDir, "test.go")

		testCode := `package main

import "fmt"

func main() {
	fmt.Println("Hello, World!")
}
`

		Convey("创建测试文件", func() {
			err := os.WriteFile(testFile, []byte(testCode), 0644)
			So(err, ShouldBeNil)

			Convey("验证文件类型识别", func() {
				ext := filepath.Ext(testFile)
				So(isCodeFile(ext), ShouldBeTrue)
			})

			Convey("执行代码检查", func() {
				cl, err := checklist.LoadChecklist("checklists/go-basic.json")
				So(err, ShouldBeNil)

				codeChecker := checker.NewCodeChecker(cl)
				report, err := codeChecker.CheckFile(testFile)

				So(err, ShouldBeNil)
				So(report, ShouldNotBeNil)
				So(report.Target, ShouldEqual, testFile)
			})
		})
	})
}
