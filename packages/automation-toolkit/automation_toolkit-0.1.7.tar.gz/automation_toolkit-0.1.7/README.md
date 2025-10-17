# Automation Toolkit

基于uiautomator2的自动化测试工具包，提供设备控制、元素定位、图像识别等功能。

## 安装

```bash
pip install automation-toolkit
```

## 类初始化参数
```python
def __init__(self, device: str, img_path: str, task_id: str = None,
             debug_img: str = None, sleep_time: int = 25, max_retries: int = 10,
             is_sleep: bool = True, accidental_processing: list = None):
```
``` text

参数	类型	默认值	说明
device	str	-	设备标识（IP地址或序列号）
img_path	str	-	图片资源路径
task_id	str	None	任务标识符（可选）
debug_img	str	"./debug_images"	调试图片保存路径（可选）
sleep_time	int	25	连接后等待时间（秒）
max_retries	int	10	最大重试次数
is_sleep	bool	True	是否在连接后等待
accidental_processing	list	None	意外弹窗处理配置（可选）
```

## 主要功能方法
### 1. 设备连接与控制
```
_connect_device(max_retries: int) -> None
功能: 连接设备

参数:

max_retries - 最大重试次数

说明: 内部方法，用于建立设备连接

open_url(url: str, time_sleep: float = 0.5) -> None
功能: 打开URL

参数:

url - 要打开的URL

time_sleep - 操作后等待时间（默认0.5秒）
```

### 2. 虚拟按键操作
``` text
virtual_key(key: str, time_sleep: float = 1) -> None
功能: 模拟虚拟按键操作

参数:

key - 按键类型 ('back', 'delete', 'enter')

time_sleep - 操作后等待时间（默认1秒）
```
### 3. 滑动操作
``` text
swipe_direction(direction: str, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None
功能: 通用滑动方法

参数:

direction - 滑动方向 ('up', 'down', 'left', 'right')

scale - 滑动比例（默认0.9）

times - 滑动次数（默认1次）

duration - 滑动持续时间（默认1.0秒）
```
#### 便捷滑动方法
``` text

方法	功能	参数说明
up(scale=0.9, times=1, duration=1.0, **kwargs)	上滑操作	同上
down(scale=0.9, times=1, duration=1.0, **kwargs)	下滑操作	同上
left(scale=0.9, times=1, duration=1.0, **kwargs)	左滑操作	同上
right(scale=0.9, times=1, duration=1.0, **kwargs)	右滑操作	同上
swipe(start_x: int, start_y: int, end_x: int, end_y: int, steps: int = 70) -> None
功能: 自定义滑动

参数:

start_x, start_y - 起始坐标

end_x, end_y - 结束坐标

steps - 滑动步数（默认70）
```

### 4. 元素定位与操作
``` text
wait_until_element_found(locator: Tuple[str, str], max_retries: int = 1, retry_interval: float = 1) -> bool
功能: 等待元素出现

参数:

locator - 元素定位器 (定位类型, 定位值)，如 ("id", "com.example.button")

max_retries - 最大重试次数（默认1次）

retry_interval - 重试间隔（默认1秒）

返回: bool - 是否找到元素

positioning_element_obj(locator: Tuple[str, str], max_retries: int = 1, report_error: int = 1) -> Optional[Any]
功能: 定位元素对象

参数:

locator - 元素定位器

max_retries - 最大重试次数

report_error - 错误报告级别 (1: 报错, 2: 不报错)

返回: 元素对象或None

click_element(locator: Tuple[str, str], max_retries: int = 1, retry_interval: float = 1, report_error: int = 1, click_type: int = 1, height_threshold: int = 1380, long_click: bool = False) -> bool
功能: 点击元素

参数:

locator - 元素定位器

max_retries - 最大重试次数

retry_interval - 点击后等待时间

report_error - 错误报告级别

click_type - 点击类型

height_threshold - 高度阈值

long_click - 是否长按

返回: bool - 是否点击成功

input_element(locator: Tuple[str, str], text: str, clear: bool = True, max_retries: int = 1, retry_interval: float = 1, report_error: int = 1) -> bool
功能: 输入文本到元素

参数:

locator - 元素定位器

text - 输入的文本

clear - 是否清空原文本（默认True）

max_retries - 最大重试次数

retry_interval - 输入后等待时间

report_error - 错误报告级别

返回: bool - 是否输入成功

send_keys(text: str, report_error: int = 1) -> bool
功能: 发送按键

参数:

text - 要输入的文本

report_error - 错误报告级别

返回: bool - 是否输入成功
```

### 5. 图像识别功能
```text
img_match(image_data: Union[str, np.ndarray, Image.Image], min_similarity: float = 0.9, debug: bool = False, region: Tuple[int, int, int, int] = None, is_recursive_call: bool = False) -> Optional[Dict[str, Any]]

功能: 图像匹配（支持区域截图）

参数:

image_data - 图像数据（路径、numpy数组或PIL图像）

min_similarity - 最小相似度阈值（默认0.9）

debug - 是否调试模式（默认False）

region - 识别区域 (x1, y1, x2, y2)（默认全屏）

is_recursive_call - 是否为递归调用（内部使用）

返回: 匹配结果字典或None

返回字典结构:
```
```TEXT
{
    "similarity": float,           # 匹配相似度
    "point": (x, y),              # 设备坐标中心点
    "match_area": (top_left, bottom_right),  # 全屏坐标匹配区域
    "screen_size": (width, height), # 设备屏幕尺寸
    "region_offset": (x, y),       # 区域偏移量
    "region": region_tuple,        # 识别区域
    "relative_coords": {           # 相对坐标信息
        "relative_center": (x, y),
        "relative_top_left": (x, y),
        "relative_bottom_right": (x, y)
    },
    "template_adjusted": bool      # 模板是否被调整过
}
```

``` text
img_click(image_data: Union[str, np.ndarray, Image.Image], min_similarity: float = 0.8, offset_x: int = 0, offset_y: int = 0, debug: bool = False, region: Tuple[int, int, int, int] = None) -> bool
功能: 图像匹配并点击

参数:

image_data - 图像数据

min_similarity - 最小相似度阈值（默认0.8）

offset_x, offset_y - 点击坐标偏移量

debug - 是否调试模式

region - 识别区域

返回: bool - 是否点击成功
```

### 6. 颜色识别功能
``` text
detect_color_in_region(target_color: Tuple[int, int, int], region: Tuple[int, int, int, int] = None, color_tolerance: int = 10, min_pixel_count: int = 1, debug: bool = False) -> Dict[str, Any]
功能: 识别指定区域内的特定颜色

参数:

target_color - 目标颜色 (R, G, B)

region - 识别区域 (x1, y1, x2, y2)（默认全屏）

color_tolerance - 颜色容差范围（默认10）

min_pixel_count - 最小像素数量阈值（默认1）

debug - 是否调试模式

返回: 识别结果字典

返回字典结构:

python
{
    "pixel_count": int,           # 匹配像素数量
    "match_ratio": float,         # 匹配比例
    "meets_threshold": bool,      # 是否满足阈值
    "total_pixels_in_region": int, # 区域总像素数
    "matched_coordinates": list,  # 匹配坐标列表
    "color_tolerance": int,       # 颜色容差
    "target_color_rgb": tuple,    # 目标颜色RGB
    "target_color_bgr": tuple,    # 目标颜色BGR
    "region": tuple              # 识别区域
}
check_point_color(point: Tuple[int, int], target_color: Tuple[int, int, int], color_tolerance: int = 5, debug: bool = False) -> Union[Tuple[int, int], bool]
功能: 检查指定点的颜色是否与目标颜色一致

参数:

point - 要检查的坐标点 (x, y)

target_color - 目标颜色 (R, G, B)

color_tolerance - 颜色容差范围（默认5）

debug - 是否调试模式

返回: 如果颜色匹配返回坐标点 (x, y)，否则返回 False

wait_for_color(target_color: Tuple[int, int, int], region: Tuple[int, int, int, int] = None, min_pixel_count: int = 1, timeout: int = 3, check_interval: float = 1.0) -> bool
功能: 等待特定颜色出现

参数:

target_color - 目标颜色

region - 识别区域

min_pixel_count - 最小像素数量

timeout - 超时时间（秒，默认3秒）

check_interval - 检查间隔（默认1.0秒）

返回: bool - 是否在超时前找到颜色

wait_for_point_color(point: Tuple[int, int], target_color: Tuple[int, int, int], color_tolerance: int = 5, timeout: int = 10, check_interval: float = 1.0) -> Union[Tuple[int, int], bool]
功能: 等待指定点的颜色变为目标颜色

参数:

point - 要检查的坐标点

target_color - 目标颜色

color_tolerance - 颜色容差（默认5）

timeout - 超时时间（秒，默认10秒）

check_interval - 检查间隔（默认1.0秒）

返回: 超时前匹配成功返回坐标点，否则返回False

check_multiple_points_color(points: List[Tuple[int, int]], target_color: Tuple[int, int, int], color_tolerance: int = 5, require_all: bool = True) -> Dict[str, Any]
功能: 检查多个点的颜色

参数:

points - 要检查的坐标点列表

target_color - 目标颜色

color_tolerance - 颜色容差

require_all - 是否要求所有点都匹配（默认True）

返回: 包含检查结果的字典

get_point_color(point: Tuple[int, int], color_format: str = "RGB") -> Optional[Tuple[int, int, int]]
功能: 获取指定坐标点的颜色值

参数:

point - 要获取颜色的坐标点 (x, y)

color_format - 颜色格式 ("RGB" 或 "BGR"，默认"RGB")

返回: 颜色值元组 (R, G, B) 或 (B, G, R)，失败返回None
```

### 7. ADB命令操作
``` TEXT
u2_adb_shell(command: str) -> str
功能: 执行u2-ADB shell命令

参数: command - 要执行的命令

返回: 命令执行结果

adb_shell(command: str) -> str
功能: 执行原生ADB shell命令

参数: command - 要执行的命令

返回: 命令执行结果

支持常用按键:

3: Home键

4: 返回键

24: 音量+

25: 音量-

66: 回车键

111: ESC键等
```

### 8. 截图功能
``` TEXT
app_screenshot(name: str, path: str = None, region: Tuple[int, int, int, int] = None) -> str
功能: 截图并使用原子操作保存

参数:

name - 截图文件名

path - 保存路径（默认使用img_path）

region - 截图区域 (x1, y1, x2, y2)

返回: 截图保存路径

error_screenshot(path) -> None
功能: 错误截图保存

参数: path - 保存路径
```

### 9. 应用管理
``` TEXT
app_operations(operation: str, package_name: str, **kwargs) -> None
功能: 应用操作通用方法

参数:

operation - 操作类型 ('install', 'uninstall', 'stop', 'start')

package_name - 应用包名

支持操作:

'install': 安装应用

'uninstall': 卸载应用

'stop': 停止应用

'start': 启动应用

app_stop_all() -> None
功能: 停止所有应用

click_coordinate(x: int, y: int, time_sleep: float = 2) -> None
功能: 点击坐标

参数:

x, y - 点击坐标

time_sleep - 点击后等待时间（默认2秒）
```

## 意外弹窗处理
工具包支持配置意外弹窗自动处理：
```PYTHON
accidental_processing = [
    {
        "popup_images": "/path/to/popup1.png",  # 弹窗识别图片（单个图片路径）
        "close_button": "/path/to/close_btn.png",  # 关闭按钮图片（可以是列表）
        "max_attempts": 2  # 最大尝试次数
    },
    {
        "popup_images": "/path/to/other_popup.png",
        "close_button": ["/path/to/close1.png", "/path/to/close2.png"],
        "max_attempts": 1
    }
]
```

## 使用示例
``` PYTHON
# 初始化工具包
toolkit = AutomationToolkit(
    device="127.0.0.1:5555",
    img_path="./images",
    task_id="test_task",
    accidental_processing=accidental_processing
)

# 图像识别点击
toolkit.img_click("button.png", min_similarity=0.8)

# 元素定位点击
toolkit.click_element(("id", "com.example.button"), max_retries=3)

# 颜色检测
result = toolkit.detect_color_in_region(
    target_color=(255, 0, 0),
    region=(100, 100, 200, 200),
    min_pixel_count=10
)

# 滑动操作
toolkit.swipe_direction("up", scale=0.8, times=2)

# 等待颜色出现
if toolkit.wait_for_color(
    target_color=(0, 255, 0),
    region=(50, 50, 100, 100),
    timeout=5
):
    print("目标颜色已出现")

# 应用操作
toolkit.app_operations("start", "com.example.app")
```
## 特性说明
``` TEXT
智能图像匹配: 支持模板尺寸自适应调整，自动处理大模板小区域情况

异常处理: 完善的错误处理和重试机制，支持多种错误报告级别

调试支持: 详细的日志记录和调试图像保存，便于问题排查

颜色识别: 精确的颜色检测和区域监控，支持多点检测

多元素支持: 支持定位和操作多个相同元素

原子操作: 截图等操作使用原子操作保证数据完整性

弹窗处理: 可配置的意外弹窗自动检测和处理机制

坐标转换: 自动处理屏幕分辨率差异和坐标转换
```

## 依赖库
``` TEXT
uiautomator2: 设备控制和UI自动化

opencv-python: 图像处理和模板匹配

Pillow: 图像处理

loguru: 日志记录

numpy: 数值计算

该工具包提供了完整的 Android 设备自动化测试解决方案，适用于各种 UI 自动化场景，特别适合游戏测试、应用自动化等功能测试需求。
```

## 找元素和找颜色的工具 uiautodev

``` text
命令行启动输入 uiauto.dev
```
