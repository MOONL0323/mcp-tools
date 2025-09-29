package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	
	"github.com/spf13/viper"
)

// Config 表示 MCP 检查器的配置
type Config struct {
	DefaultChecklist string            `mapstructure:"default_checklist" json:"default_checklist"`
	Checklists       map[string]string `mapstructure:"checklists" json:"checklists"` // name -> file_path
}

const (
	ConfigDir     = "configs"
	DefaultConfig = "default"
	ConfigType    = "json"
	ChecklistDir  = "checklists"
)

var (
	globalViper *viper.Viper
)

// InitViper 初始化 Viper 配置
func InitViper() error {
	globalViper = viper.New()
	
	// 设置配置文件
	globalViper.SetConfigName(DefaultConfig)
	globalViper.SetConfigType(ConfigType)
	globalViper.AddConfigPath(ConfigDir)
	globalViper.AddConfigPath(".")
	
	// 设置环境变量前缀
	globalViper.SetEnvPrefix("MCP")
	globalViper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	globalViper.AutomaticEnv()
	
	// 设置默认值
	setDefaults()
	
	// 读取配置文件
	if err := globalViper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			// 配置文件不存在，创建默认配置
			return createDefaultConfig()
		}
		return fmt.Errorf("读取配置文件失败: %w", err)
	}
	
	return nil
}

// setDefaults 设置默认配置值
func setDefaults() {
	globalViper.SetDefault("default_checklist", "go-basic")
	globalViper.SetDefault("checklists", map[string]string{
		"go-basic": "checklists/go-basic.json",
	})
}

// LoadConfig 加载配置文件
func LoadConfig() (*Config, error) {
	if globalViper == nil {
		if err := InitViper(); err != nil {
			return nil, err
		}
	}
	
	var config Config
	if err := globalViper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}
	
	return &config, nil
}

// LoadConfigFromFile 从指定文件加载配置（用于测试）
func LoadConfigFromFile(configFile string) (*Config, error) {
	v := viper.New()
	
	// 解析文件路径
	dir := filepath.Dir(configFile)
	filename := filepath.Base(configFile)
	ext := filepath.Ext(filename)
	name := strings.TrimSuffix(filename, ext)
	
	v.SetConfigName(name)
	v.SetConfigType(strings.TrimPrefix(ext, "."))
	v.AddConfigPath(dir)
	
	// 设置默认值
	setViperDefaults(v)
	
	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("读取配置文件 %s 失败: %w", configFile, err)
	}
	
	var config Config
	if err := v.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("解析配置文件 %s 失败: %w", configFile, err)
	}
	
	return &config, nil
}

// setViperDefaults 为指定的 viper 实例设置默认值
func setViperDefaults(v *viper.Viper) {
	v.SetDefault("default_checklist", "go-basic")
	v.SetDefault("checklists", map[string]string{
		"go-basic": "checklists/go-basic.json",
	})
}

// SaveConfig 保存配置文件
func (c *Config) SaveConfig() error {
	if globalViper == nil {
		return fmt.Errorf("Viper 未初始化")
	}
	
	// 更新 viper 中的值
	globalViper.Set("default_checklist", c.DefaultChecklist)
	globalViper.Set("checklists", c.Checklists)
	
	return globalViper.WriteConfig()
}

// SaveConfigToFile 保存配置到指定文件（用于测试）
func SaveConfigToFile(config *Config, configFile string) error {
	v := viper.New()
	
	// 解析文件路径
	dir := filepath.Dir(configFile)
	filename := filepath.Base(configFile)
	ext := filepath.Ext(filename)
	name := strings.TrimSuffix(filename, ext)
	
	v.SetConfigName(name)
	v.SetConfigType(strings.TrimPrefix(ext, "."))
	v.AddConfigPath(dir)
	
	// 设置配置值
	v.Set("default_checklist", config.DefaultChecklist)
	v.Set("checklists", config.Checklists)
	
	return v.WriteConfigAs(configFile)
}

// AddChecklist 添加新的检查清单
func (c *Config) AddChecklist(name, filePath string) {
	if c.Checklists == nil {
		c.Checklists = make(map[string]string)
	}
	c.Checklists[name] = filePath
}

// SetDefaultChecklist 设置默认检查清单
func (c *Config) SetDefaultChecklist(name string) error {
	if _, exists := c.Checklists[name]; !exists {
		return fmt.Errorf("检查清单 '%s' 不存在", name)
	}
	c.DefaultChecklist = name
	return nil
}

// GetChecklistPath 获取检查清单文件路径
func (c *Config) GetChecklistPath(name string) (string, error) {
	if name == "" {
		name = c.DefaultChecklist
	}
	
	if name == "" {
		return "", fmt.Errorf("没有指定检查清单且没有设置默认检查清单")
	}
	
	path, exists := c.Checklists[name]
	if !exists {
		return "", fmt.Errorf("检查清单 '%s' 不存在", name)
	}
	
	return path, nil
}

// ListChecklists 列出所有检查清单
func (c *Config) ListChecklists() map[string]string {
	return c.Checklists
}

// createDefaultConfig 创建默认配置
func createDefaultConfig() error {
	if globalViper == nil {
		globalViper = viper.New()
		globalViper.SetConfigName(DefaultConfig)
		globalViper.SetConfigType(ConfigType)
		globalViper.AddConfigPath(ConfigDir)
		globalViper.AddConfigPath(".")
	}
	
	// 设置默认值
	setDefaults()
	
	// 确保配置目录存在
	configPath := filepath.Join(ConfigDir, DefaultConfig+"."+ConfigType)
	dir := filepath.Dir(configPath)
	
	// 创建目录（如果不存在）
	if err := createDirIfNotExists(dir); err != nil {
		return fmt.Errorf("创建配置目录失败: %w", err)
	}
	
	// 写入配置文件
	return globalViper.WriteConfigAs(configPath)
}

// createDirIfNotExists 创建目录（如果不存在）
func createDirIfNotExists(dir string) error {
	// 简化实现，直接使用 os 包
	info, err := os.Stat(dir)
	if os.IsNotExist(err) {
		return os.MkdirAll(dir, 0755)
	}
	if err != nil {
		return err
	}
	if !info.IsDir() {
		return fmt.Errorf("%s 不是目录", dir)
	}
	return nil
}

// ReloadConfig 重新加载配置
func ReloadConfig() error {
	if globalViper == nil {
		return InitViper()
	}
	return globalViper.ReadInConfig()
}

// GetViperInstance 获取全局 Viper 实例（用于高级配置）
func GetViperInstance() *viper.Viper {
	return globalViper
}