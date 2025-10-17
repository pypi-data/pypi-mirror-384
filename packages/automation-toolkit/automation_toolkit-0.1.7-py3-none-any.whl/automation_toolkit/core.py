import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from time import sleep
from typing import Union, Tuple, List, Optional, Dict, Any

import cnocr
import uiautomator2 as u2
import cv2
import numpy as np
from PIL import Image
from loguru import logger

# 添加CnOCR导入
try:
    from cnocr import CnOcr
    CNOCR_AVAILABLE = True
except ImportError:
    CNOCR_AVAILABLE = False
    logger.warning("CnOCR未安装，文字识别功能不可用")


class AutomationToolkit:
    """
    自动化测试工具包，提供设备控制、元素定位、图像识别等功能

    Args:
        device: 设备标识（IP地址或序列号）
        img_path: 图片资源路径
        task_id: 任务标识符
        debug_img: 调试图片保存路径
        sleep_time: 连接后等待时间
        max_retries: 最大重试次数
        is_sleep: 是否在连接后等待
        accidental_processing: 意外弹窗处理配置
    """

    def __init__(self, device: str, img_path: str, task_id: str = None,
                 debug_img: str = None,  max_retries: int = 10,
                  accidental_processing: list = None) -> None:

        self.device = device
        self.task_id = task_id or "default"
        self.img_path = img_path
        self.debug_img = debug_img or "./debug_images"
        self.accidental_processing = accidental_processing
        self.last_debug_image = None

        # 创建必要的目录
        os.makedirs(self.debug_img, exist_ok=True)
        os.makedirs(self.img_path, exist_ok=True)

        # 初始化OCR
        self.ocr_engine =cnocr.CnOcr()
        # 设备连接
        self._connect_device(max_retries)

    def _connect_device(self, max_retries: int) -> None:
        """连接设备"""
        for i in range(max_retries):
            try:
                self.d = u2.connect(self.device)
                logger.debug(f'成功连接到设备: {self.device}')
                break
            except Exception as e:
                logger.warning(f'第{i + 1}次连接失败: {e}')
                if i == max_retries - 1:
                    raise ConnectionError(f'无法连接到设备 {self.device}') from e
                sleep(1)

    def ocr_find_text(self, target_text: str,
                      region: Tuple[int, int, int, int] = None,
                      debug: bool = False) -> Union[Dict[str, Any], bool]:
        """
        使用OCR识别文字位置，计算目标文字在文本框内的精确位置
        """
        if self.ocr_engine is None:
            logger.error("OCR引擎未初始化，无法进行文字识别")
            return False

        try:
            # 获取屏幕截图
            screenshot = self.d.screenshot(format='opencv')
            if screenshot is None:
                logger.error("无法获取屏幕截图")
                return False

            # 保存全屏截图形状
            full_screenshot_shape = screenshot.shape

            # 如果指定了区域，裁剪截图
            if region:
                x1, y1, x2, y2 = region
                # 确保区域在有效范围内
                height, width = screenshot.shape[:2]
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(x1 + 1, min(x2, width))
                y2 = max(y1 + 1, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    logger.error(f"无效的区域设置: {region}")
                    return False

                region_screenshot = screenshot[y1:y2, x1:x2]
                region_offset = (x1, y1)
                # 使用区域截图进行OCR
                ocr_screenshot = region_screenshot
            else:
                region_screenshot = screenshot
                region_offset = (0, 0)
                # 使用全屏截图进行OCR
                ocr_screenshot = screenshot

            # 重要：将BGR转换为RGB
            if len(ocr_screenshot.shape) == 3 and ocr_screenshot.shape[2] == 3:
                region_screenshot_rgb = cv2.cvtColor(ocr_screenshot, cv2.COLOR_BGR2RGB)
            else:
                # 如果是灰度图或单通道图，先转换为BGR再转RGB
                if len(ocr_screenshot.shape) == 2:
                    ocr_screenshot = cv2.cvtColor(ocr_screenshot, cv2.COLOR_GRAY2BGR)
                region_screenshot_rgb = cv2.cvtColor(ocr_screenshot, cv2.COLOR_BGR2RGB)

            if debug:
                # 保存转换前后的图像用于调试
                cv2.imwrite('debug_bgr.png', ocr_screenshot)
                cv2.imwrite('debug_rgb.png', cv2.cvtColor(region_screenshot_rgb, cv2.COLOR_RGB2BGR))

            # 使用OCR识别文字（传入RGB图像）
            ocr_results = self.ocr_engine.ocr(region_screenshot_rgb)

            if debug:
                logger.debug(f"OCR识别结果: {ocr_results}")

            # 如果没有识别到任何结果，尝试其他处理方式
            if not ocr_results:
                logger.debug(f"{self.task_id}--未识别到任何文字，尝试图像预处理...")

                # 尝试图像增强
                enhanced_image = self._enhance_image(region_screenshot_rgb)
                ocr_results = self.ocr_engine.ocr(enhanced_image)

                if debug and not ocr_results:
                    cv2.imwrite('debug_enhanced.png', cv2.cvtColor(enhanced_image, cv2.COLOR_RGB2BGR))

            # 遍历识别结果，查找包含目标文字的结果
            for result in ocr_results:
                if isinstance(result, dict) and 'text' in result:
                    text = result['text']
                    confidence = result.get('score', 0.0)
                    position = result.get('position', [])

                    logger.debug(f"OCR识别到文字: '{text}', 置信度: {confidence:.3f}, 位置: {position}")

                    # 检查是否包含目标文字
                    if target_text in text:
                        # 计算目标文字在文本框内的精确位置
                        logger.debug(f"找到包含目标文字 '{target_text}' 的文本: '{text}'")
                        target_position = self._calculate_target_text_position(
                            text, target_text, position, region_offset, full_screenshot_shape
                        )

                        result_info = {
                            'text': text,
                            'target_text': target_text,
                            'confidence': confidence,
                            'position': position,  # 整个文本框的位置
                            'target_position': target_position,  # 目标文字的精确位置
                            'screen_position': target_position['screen_position'],  # 屏幕绝对位置
                            'center_point': target_position['screen_position']['center'],
                            'region': region if region else (0, 0, screenshot.shape[1], screenshot.shape[0]),
                            'region_offset': region_offset
                        }

                        logger.info(
                            f"{self.task_id}--找到目标文字: '{target_text}' "
                            f"(在文字 '{text}' 中), 置信度: {confidence:.3f}, "
                            f"目标文字中心位置: {target_position['screen_position']['center']}"
                        )

                        if debug:
                            self._save_ocr_debug_image(
                                ocr_screenshot, result, target_position['screen_position'],
                                target_text, region_offset
                            )

                        return result_info

            logger.debug(f"{self.task_id}--未找到目标文字: '{target_text}'")
            return False

        except Exception as e:
            logger.error(f"{self.task_id}--OCR文字识别失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def _enhance_image(self, image):
        """图像增强处理"""
        try:
            # 对比度增强
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced_lab = cv2.merge([l, a, b])
            enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)

            return enhanced_image
        except Exception as e:
            logger.warning(f"图像增强失败: {e}")
            return image

    def _calculate_target_text_position(self, full_text: str, target_text: str,
                                        textbox_position, region_offset, full_screenshot_shape):
        """
        计算目标文字在文本框内的精确位置

        Args:
            full_text: OCR识别到的完整文本
            target_text: 要查找的目标文字
            textbox_position: 整个文本框的位置
            region_offset: 区域偏移量
            full_screenshot_shape: 全屏截图形状
        """
        try:
            # 找到目标文字在完整文本中的位置
            start_index = full_text.find(target_text)
            if start_index == -1:
                logger.error(f"目标文字 '{target_text}' 不在文本 '{full_text}' 中")
                return None

            end_index = start_index + len(target_text)

            # 计算目标文字在文本框中的相对位置（按字符比例）
            text_length = len(full_text)
            if text_length == 0:
                return None

            # 获取文本框的四个点坐标
            if hasattr(textbox_position, 'tolist'):
                textbox_position = textbox_position.tolist()

            if isinstance(textbox_position, list) and len(textbox_position) == 4:
                # 文本框的四个点：左上、右上、右下、左下
                left_top = textbox_position[0]  # [x1, y1]
                right_top = textbox_position[1]  # [x2, y2]
                right_bottom = textbox_position[2]  # [x3, y3]
                left_bottom = textbox_position[3]  # [x4, y4]

                # 计算文本框的宽度（取上边和下边的平均值）
                top_width = right_top[0] - left_top[0]
                bottom_width = right_bottom[0] - left_bottom[0]
                avg_width = (top_width + bottom_width) / 2

                # 计算每个字符的大概宽度
                char_width = avg_width / text_length

                # 计算目标文字的起始和结束位置（在文本框内的相对位置）
                target_start_x = left_top[0] + (start_index * char_width)
                target_end_x = left_top[0] + (end_index * char_width)

                # 目标文字的高度（取文本框高度）
                target_top_y = min(left_top[1], right_top[1])
                target_bottom_y = max(left_bottom[1], right_bottom[1])

                # 计算目标文字的中心点（在区域内的相对位置）
                target_center_x = (target_start_x + target_end_x) / 2
                target_center_y = (target_top_y + target_bottom_y) / 2

                # 转换为屏幕绝对坐标
                x_offset, y_offset = region_offset
                screen_bbox = (
                    target_start_x + x_offset,
                    target_top_y + y_offset,
                    target_end_x + x_offset,
                    target_bottom_y + y_offset
                )
                screen_center = (
                    int(target_center_x + x_offset),
                    int(target_center_y + y_offset)
                )

                target_position = {
                    'relative_bbox': (target_start_x, target_top_y, target_end_x, target_bottom_y),
                    'relative_center': (target_center_x, target_center_y),
                    'screen_position': {
                        'bbox': screen_bbox,
                        'center': screen_center
                    }
                }

                logger.debug(f"目标文字位置计算 - 文本: '{full_text}', 目标: '{target_text}'")
                logger.debug(f"起始索引: {start_index}, 字符宽度: {char_width:.2f}")
                logger.debug(f"相对位置: {target_position['relative_bbox']}")
                logger.debug(f"屏幕位置: {screen_bbox}")

                return target_position

            else:
                logger.error(f"无效的文本框位置格式: {textbox_position}")
                return None

        except Exception as e:
            logger.error(f"计算目标文字位置时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _save_ocr_debug_image(self, screenshot, ocr_result, screen_position,
                              target_text, region_offset):
        """保存OCR调试图像"""
        try:
            debug_img = screenshot.copy()

            # 绘制文字边界框
            if (screen_position.get('bounding_box') and
                    screen_position['bounding_box'].get('top_left_relative')):
                top_left = screen_position['bounding_box']['top_left_relative']
                bottom_right = screen_position['bounding_box']['bottom_right_relative']

                # 绘制边界框
                cv2.rectangle(debug_img, top_left, bottom_right, (0, 255, 0), 2)

                # 绘制中心点
                center = screen_position['center']
                center_relative = (center[0] - region_offset[0], center[1] - region_offset[1])
                cv2.drawMarker(debug_img, center_relative, (0, 0, 255),
                               cv2.MARKER_CROSS, 20, 2)

            # 添加文本信息
            text = ocr_result.get('text', '')
            confidence = ocr_result.get('score', 0.0)

            info_lines = [
                f"Target: {target_text}",
                f"Found: {text}",
                f"Confidence: {confidence:.3f}",
                f"Center: {screen_position['center']}"
            ]

            for i, line in enumerate(info_lines):
                cv2.putText(debug_img, line, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(debug_img, line, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"ocr_debug_{timestamp}.png")
            cv2.imwrite(debug_path, debug_img)

            logger.debug(f"{self.task_id}--OCR调试图像已保存: {debug_path}")

        except Exception as e:
            logger.warning(f"{self.task_id}--保存OCR调试图像失败: {e}")

    def ocr_click_text(self, target_text: str,
                       region: Tuple[int, int, int, int] = None,
                       offset_x: int = 0,
                       offset_y: int = 0) -> bool:
        """
        使用OCR找到文字并点击

        Args:
            target_text: 要点击的目标文字
            region: 识别区域
            offset_x: X轴偏移
            offset_y: Y轴偏移

        Returns:
            bool: 是否点击成功
        """
        result = self.ocr_find_text(target_text, region)

        if not result:
            logger.debug(f"{self.task_id}--未找到可点击的文字: '{target_text}'")
            return False

        try:
            center_x, center_y = result['center_point']
            target_x = center_x + offset_x
            target_y = center_y + offset_y

            self.d.click(target_x, target_y)
            logger.info(
                f"{self.task_id}--OCR点击文字 '{target_text}' "
                f"位置: ({target_x}, {target_y})"
            )
            time.sleep(1.5)
            return True

        except Exception as e:
            logger.error(f"{self.task_id}--OCR点击文字失败: {e}")
            return False


    def open_url(self, url: str, time_sleep: float = 0.5) -> None:
        """打开URL"""
        self.d.open_url(url)
        logger.debug(f'{self.task_id}--打开链接: {url}')
        sleep(time_sleep)

    def virtual_key(self, key: str, time_sleep: float = 1) -> None:
        """
        模拟虚拟按键操作

        Args:
            key: 按键类型 ('back', 'delete', 'enter')
            time_sleep: 操作后等待时间
        """
        valid_keys = {'back', 'delete', 'enter'}
        if key not in valid_keys:
            logger.warning(f'不支持的按键类型: {key}, 支持的按键: {valid_keys}')
            return

        if key == 'delete':
            for _ in range(30):
                self.d.press(key)
        else:
            self.d.press(key)

        logger.debug(f'{self.task_id}--执行 {key} 操作，等待 {time_sleep} 秒')
        sleep(time_sleep)

    def swipe_direction(self, direction: str, scale: float = 0.9,
                        times: int = 1, duration: float = 1.0, **kwargs) -> None:
        """
        通用滑动方法

        Args:
            direction: 滑动方向 ('up', 'down', 'left', 'right')
            scale: 滑动比例
            times: 滑动次数
            duration: 滑动持续时间
        """
        valid_directions = {'up', 'down', 'left', 'right'}
        if direction not in valid_directions:
            logger.warning(f'{self.task_id}--不支持的滑动方向: {direction}')
            return

        for _ in range(times):
            self.d.swipe_ext(direction, scale, duration=duration, **kwargs)

        sleep(times)
        logger.debug(f'{self.task_id}--向{direction}滑动成功')

    def up(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
        """上滑操作"""
        self.swipe_direction('up', scale, times, duration, **kwargs)

    def down(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
        """下滑操作"""
        self.swipe_direction('down', scale, times, duration, **kwargs)

    def left(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
        """左滑操作"""
        self.swipe_direction('left', scale, times, duration, **kwargs)

    def right(self, scale: float = 0.9, times: int = 1, duration: float = 1.0, **kwargs) -> None:
        """右滑操作"""
        self.swipe_direction('right', scale, times, duration, **kwargs)

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              steps: int = 70) -> None:
        """自定义滑动"""
        self.d.swipe(start_x, start_y, end_x, end_y, steps=steps)
        # time.sleep(1)
        logger.debug(f'{self.task_id}--从({start_x},{start_y})滑动到({end_x},{end_y})')

    def wait_until_element_found(self, locator: Tuple[str, str],
                                 max_retries: int = 1, retry_interval: float = 1) -> bool:
        """
        等待元素出现

        Args:
            locator: 元素定位器 (定位类型, 定位值)
            max_retries: 最大重试次数
            retry_interval: 重试间隔

        Returns:
            bool: 是否找到元素
        """
        if not isinstance(locator, tuple) or len(locator) != 2:
            logger.error(f'{self.task_id}--元素定位器格式错误: {locator}')
            return False

        locator_type, locator_value = locator

        if locator_type not in {'xpath', 'id'}:
            logger.error(f'{self.task_id}--不支持的定位类型: {locator_type}')
            return False

        for i in range(max_retries):
            element = self.d.xpath(locator_value) if locator_type == 'xpath' else self.d(resourceId=locator_value)

            if element.exists:
                logger.debug(f'{self.task_id}--找到元素: {locator_value}')
                return True

            if i < max_retries - 1:
                logger.debug(f'{self.task_id}--未找到元素: {locator_value}, 第{i + 1}次重试')
                sleep(retry_interval)

        logger.debug(f'{self.task_id}--未找到元素: {locator}, 超出最大重试次数 {max_retries}')
        return False

    def _get_element_object(self, locator: Tuple[str, str]) -> Optional[Any]:
        """获取元素对象"""
        locator_type, locator_value = locator
        if locator_type == 'id':
            return self.d(resourceId=locator_value)
        elif locator_type == 'xpath':
            return self.d.xpath(locator_value)
        return None

    def positioning_element_obj(self, locator: Tuple[str, str], max_retries: int = 1,
                                report_error: int = 1) -> Optional[Any]:
        """
        定位元素对象

        Args:
            locator: 元素定位器
            max_retries: 最大重试次数
            report_error: 错误报告级别 (1: 报错, 2: 不报错)

        Returns:
            Optional[Any]: 元素对象或None
        """
        found = self.wait_until_element_found(locator, max_retries)

        if found:
            return self._get_element_object(locator)

        if report_error == 1:
            raise Exception(f'{self.task_id}--定位元素失败: {locator}')
        else:
            logger.debug(f'{self.task_id}--未找到元素: {locator}, 忽略错误')
            return None

    def click_element(self, locator: Tuple[str, str], max_retries: int = 1,
                      retry_interval: float = 1, report_error: int = 1,
                      click_type: int = 1, height_threshold: int = 1380,
                      long_click: bool = False) -> bool:
        """
        点击元素

        Args:
            locator: 元素定位器
            max_retries: 最大重试次数
            retry_interval: 点击后等待时间
            report_error: 错误报告级别
            click_type: 点击类型
            height_threshold: 高度阈值
            long_click: 是否长按

        Returns:
            bool: 是否点击成功
        """
        element_obj = self.positioning_element_obj(
            locator, max_retries, report_error
        )

        if not element_obj:
            return False

        sleep(0.5)

        # 处理需要滚动的情况
        if click_type == 2:
            try:
                bounds = element_obj.bounds
                element_center_y = (bounds[1] + bounds[3]) / 2
                if element_center_y >= height_threshold:
                    self.up(0.3, duration=0.1)
            except Exception as e:
                logger.warning(f'{self.task_id}--获取元素位置失败: {e}')

        # 执行点击操作
        try:
            if long_click:
                element_obj.long_click()
            else:
                element_obj.click()

            sleep(retry_interval)
            logger.debug(f'{self.task_id}--点击元素成功: {locator}')
            return True

        except Exception as e:
            logger.error(f'{self.task_id}--点击元素失败: {e}')
            if report_error == 1:
                raise Exception(f'{self.task_id}--点击元素失败: {e}')
            return False

    def input_element(self, locator: Tuple[str, str], text: str, clear: bool = True,
                      max_retries: int = 1, retry_interval: float = 1,
                      report_error: int = 1) -> bool:
        """
        输入文本到元素

        Args:
            locator: 元素定位器
            text: 输入的文本
            clear: 是否清空原文本
            max_retries: 最大重试次数
            retry_interval: 输入后等待时间
            report_error: 错误报告级别

        Returns:
            bool: 是否输入成功
        """
        element_obj = self.positioning_element_obj(
            locator, max_retries, report_error
        )

        if not element_obj:
            return False

        try:
            if clear:
                element_obj.clear_text()

            element_obj.set_text(text)
            sleep(retry_interval)
            logger.debug(f'{self.task_id}--输入文本成功: {text}')
            return True

        except Exception as e:
            logger.error(f'{self.task_id}--输入文本失败: {e}')
            if report_error == 1:
                raise
            return False

    def send_keys(self, text: str, report_error: int = 1) -> bool:
        """发送按键"""
        try:
            self.d.send_keys(text, clear=report_error != 1)
            logger.debug(f'{self.task_id}--输入文本: {text}')
            return True
        except Exception as e:
            logger.error(f'{self.task_id}--输入文本失败: {e}')
            if report_error == 1:
                raise
            return False

    def u2_adb_shell(self, command: str) -> str:
        """执行u2-ADB shell命令"""
        result = self.d.shell(command)
        sleep(1)
        return result.output

    def adb_shell(self, command: str) -> str:

        # subprocess.run(['adb', '-s', 'RF8N90WF4ZN', 'shell', 'input', 'keyevent', '111'], check=False)
        """执行原生ADB shell命令
            Args:
                command: 要执行的ADB shell命令
                3: Home键
                4: 返回键
                5: 电话拨号
                6: 挂断电话
                24: 音量+
                25: 音量-
                26: 电源键
                27: 相机
                66: 回车键
                67: 退格键
                82: 菜单键
                84: 搜索键
                111: ESC键
            # Returns:
            #     str: 命令执行结果
            Raises:
                Exception: 当命令执行失败时抛出异常
            """
        try:
            # 构建完整的ADB命令
            full_command = ['adb', '-s', self.device, 'shell'] + command.split()
            # 执行命令并获取结果
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 设置超时时间
            )
            #
            logger.debug(f"{self.task_id}--{self.device}ADB命令成功: {command}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception(f"ADB命令执行超时: {command}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"ADB命令执行失败: {command}, 错误: {e.stderr}")
        except Exception as e:
            raise Exception(f"执行ADB命令时发生未知错误: {e}")

    def positioning_element_list_obj(self, locator: Tuple[str, str], max_retries: int = 10,
                                     report_error: int = 1) -> Optional[List[Any]]:
        """
        定位多个元素对象

        Returns:
            Optional[List[Any]]: 元素对象列表或None
        """
        found = self.wait_until_element_found(locator, max_retries)

        if found:
            element_obj = self._get_element_object(locator)
            return element_obj.all() if hasattr(element_obj, 'all') else [element_obj]

        if report_error == 1:
            raise Exception(f'{self.task_id}--定位元素失败: {locator}')
        else:
            logger.debug(f'{self.task_id}--未找到元素: {locator}, 忽略错误')
            return None

    def _load_image(self, image_data: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """加载并统一图像格式为3通道BGR"""
        if isinstance(image_data, str):
            image_path = os.path.join(self.img_path, image_data)
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is None:
                raise FileNotFoundError(f"{self.task_id}--无法加载图像: '{image_path}'")
        elif isinstance(image_data, np.ndarray):
            image = image_data
        elif isinstance(image_data, Image.Image):
            image = np.array(image_data)
        else:
            raise TypeError(f"不支持的图像类型: {type(image_data)}")

        # 处理图像通道
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 4:
            # RGBA转BGR
            bg = np.ones_like(image[..., :3]) * 255
            rgb = image[..., :3]
            alpha = image[..., 3:] / 255.0
            image = (alpha * rgb + (1 - alpha) * bg).astype(np.uint8)
        elif image.ndim == 3 and image.shape[2] == 3:
            pass  # 已经是BGR格式
        else:
            raise ValueError(f"{self.task_id}--不支持的图像格式: {image.shape}")
        return image

    def img_match(self, image_data: Union[str, np.ndarray, Image.Image],
                  min_similarity: float = 0.9, debug: bool = False,
                  region: Tuple[int, int, int, int] = None,
                  is_recursive_call: bool = False) -> Optional[Dict[str, Any]]:
        """
        图像匹配（支持区域截图）
        改进版本：更好地处理模板尺寸大于截图区域的情况
        accidental_processing 意外弹窗检查与处理
        is_recursive_call 标记是否为递归调用（避免重复处理意外弹窗）
        """
        try:
            template = self._load_image(image_data)
            template_height, template_width = template.shape[:2]

            # 获取设备信息
            device_width, device_height = self.d.window_size()

            # 获取全屏截图（用于计算缩放比例）
            full_screenshot = self.d.screenshot(format='opencv')
            full_height, full_width = full_screenshot.shape[:2]

            # 计算全屏的缩放比例（固定值）
            scale_x = device_width / full_width
            scale_y = device_height / full_height

            # 获取目标截图（支持区域截图）
            if region:
                x1, y1, x2, y2 = region
                # 确保区域在截图范围内
                x1 = max(0, min(x1, full_width - 1))
                y1 = max(0, min(y1, full_height - 1))
                x2 = max(x1 + 1, min(x2, full_width))
                y2 = max(y1 + 1, min(y2, full_height))

                # 检查区域是否有效
                if x2 <= x1 or y2 <= y1:
                    logger.warning(f"{self.task_id}--无效的区域设置: {region}")
                    return None

                screenshot = full_screenshot[y1:y2, x1:x2]
                region_offset = (x1, y1)
            else:
                screenshot = full_screenshot
                region_offset = (0, 0)

            screenshot_height, screenshot_width = screenshot.shape[:2]

            # 检查截图区域是否有效
            if screenshot_width <= 0 or screenshot_height <= 0:
                logger.warning(f"{self.task_id}--截图区域无效: {screenshot_width}x{screenshot_height}")
                return None

            # 检查模板是否大于截图区域
            template_too_large = False
            if template_width > screenshot_width or template_height > screenshot_height:
                logger.warning(
                    f"{self.task_id}--模板尺寸({template_width}x{template_height})大于截图区域({screenshot_width}x{screenshot_height})")
                template_too_large = True

                # 调整模板大小以适应截图区域
                scale_factor = min(screenshot_width / template_width, screenshot_height / template_height)
                new_width = max(10, int(template_width * scale_factor * 0.95))  # 稍微缩小一点确保完全在区域内
                new_height = max(10, int(template_height * scale_factor * 0.95))

                if new_width < 10 or new_height < 10:
                    logger.warning(f"{self.task_id}--调整后的模板尺寸太小({new_width}x{new_height})，无法匹配")
                    return None

                # 使用高质量的重采样方法
                template = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_AREA)
                template_height, template_width = template.shape[:2]
                logger.debug(f"{self.task_id}--模板已调整为: {template_width}x{template_height}")

            # 如果模板仍然太大，使用边缘裁剪策略
            if template_width > screenshot_width or template_height > screenshot_height:
                logger.warning(f"{self.task_id}--模板调整后仍然太大，尝试边缘裁剪")

                # 计算需要裁剪的边缘
                width_excess = max(0, template_width - screenshot_width)
                height_excess = max(0, template_height - screenshot_height)

                # 从中心裁剪模板
                start_x = width_excess // 2
                start_y = height_excess // 2
                end_x = template_width - (width_excess - start_x)
                end_y = template_height - (height_excess - start_y)

                if end_x > start_x and end_y > start_y:
                    template = template[start_y:end_y, start_x:end_x]
                    template_height, template_width = template.shape[:2]
                    logger.debug(f"{self.task_id}--模板裁剪后尺寸: {template_width}x{template_height}")
                else:
                    logger.warning(f"{self.task_id}--模板裁剪失败，尺寸仍然不匹配")
                    return None

            if debug:
                logger.debug(f"{self.task_id}--设备分辨率: {device_width}x{device_height}")
                logger.debug(f"{self.task_id}--全屏截图尺寸: {full_width}x{full_height}")
                logger.debug(f"{self.task_id}--目标截图尺寸: {screenshot_width}x{screenshot_height}")
                logger.debug(f"{self.task_id}--模板尺寸: {template_width}x{template_height}")
                logger.debug(f"{self.task_id}--缩放比例: x:{scale_x:.2f}, y:{scale_y:.2f}")
                if region:
                    logger.debug(f"{self.task_id}--截图区域: {region}, 区域偏移: {region_offset}")
                if template_too_large:
                    logger.debug(f"{self.task_id}--模板曾被调整大小")

            # 执行模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 只在非递归调用时处理意外弹窗
            if max_val < min_similarity and not is_recursive_call:
                if self.accidental_processing:
                    logger.debug(f"{self.task_id}--匹配失败，开始意外弹窗处理")
                    # 处理意外弹窗
                    processed = self._handle_accidental_popups(self.accidental_processing)
                    if processed:
                        # 弹窗处理后重新尝试匹配（标记为递归调用）
                        logger.debug(f"{self.task_id}--弹窗处理后重新尝试匹配")
                        return self.img_match(
                            image_data=image_data,
                            min_similarity=min_similarity,
                            debug=debug,
                            region=region,
                            is_recursive_call=True  # 标记为递归调用，避免重复处理
                        )

                if debug:
                    logger.warning(f"{self.task_id}--匹配失败 - 相似度: {max_val:.2f} < 阈值: {min_similarity:.2f}")
                return None

            # 如果是递归调用且仍然匹配失败，直接返回
            if max_val < min_similarity and is_recursive_call:
                if debug:
                    logger.warning(f"{self.task_id}--递归调用后仍然匹配失败 - 相似度: {max_val:.2f}")
                return None

            # 计算匹配区域和中心点（相对于截图区域）
            top_left_relative = max_loc
            bottom_right_relative = (top_left_relative[0] + template_width, top_left_relative[1] + template_height)
            center_x_relative = (top_left_relative[0] + bottom_right_relative[0]) // 2
            center_y_relative = (top_left_relative[1] + bottom_right_relative[1]) // 2

            # 转换为全屏坐标（考虑区域偏移）
            top_left_full = (top_left_relative[0] + region_offset[0], top_left_relative[1] + region_offset[1])
            bottom_right_full = (bottom_right_relative[0] + region_offset[0],
                                 bottom_right_relative[1] + region_offset[1])
            center_x_full = center_x_relative + region_offset[0]
            center_y_full = center_y_relative + region_offset[1]

            # 转换为设备坐标（使用全屏的缩放比例）
            phys_x = int(center_x_full * scale_x)
            phys_y = int(center_y_full * scale_y)

            logger.debug(
                f"{self.task_id}--匹配相似度: {max_val:.2f} - {image_data if isinstance(image_data, str) else '图像'}")

            if debug:
                # 保存调试图像（显示匹配区域）
                debug_img = screenshot.copy()
                cv2.rectangle(debug_img, top_left_relative, bottom_right_relative, (0, 0, 255), 2)
                cv2.drawMarker(debug_img, (center_x_relative, center_y_relative), (0, 255, 0), cv2.MARKER_CROSS, 30, 2)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_path = os.path.join(self.debug_img, f"debug_match_{timestamp}.png")
                cv2.imwrite(debug_path, debug_img)
                self.last_debug_image = debug_path
                logger.debug(f"{self.task_id}--调试图像已保存: {debug_path}")

            return {
                "similarity": max_val,
                "point": (phys_x, phys_y),  # 设备坐标中心点
                "match_area": (top_left_full, bottom_right_full),  # 全屏坐标匹配区域
                "screen_size": (device_width, device_height),
                "region_offset": region_offset,
                "region": region if region else (0, 0, full_width, full_height),
                "relative_coords": {  # 添加相对坐标信息用于调试
                    "relative_center": (center_x_relative, center_y_relative),
                    "relative_top_left": top_left_relative,
                    "relative_bottom_right": bottom_right_relative
                },
                "template_adjusted": template_too_large  # 标记模板是否被调整过
            }

        except Exception as e:
            logger.error(f"{self.task_id}--图像匹配失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def compare_region_similarity(self, full_image_data: Union[str, np.ndarray, Image.Image],
                                  region: Tuple[int, int, int, int],
                                  min_similarity: float = 0.8,
                                  debug: bool = False) -> bool:
        """
        比较指定区域的图片相似度

        Args:
            full_image_data: 完整的原图片数据（路径、numpy数组或PIL图像）
            region: 截取区域 (x1, y1, x2, y2)
            min_similarity: 最小相似度阈值（默认0.8）
            debug: 是否调试模式

        Returns:
            bool: 相似度是否达到阈值
        """
        try:
            # 1. 从原图片中截取指定区域作为模板
            full_image = self._load_image(full_image_data)
            x1, y1, x2, y2 = region

            # 确保区域在图片范围内
            img_height, img_width = full_image.shape[:2]
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(x1 + 1, min(x2, img_width))
            y2 = max(y1 + 1, min(y2, img_height))

            if x2 <= x1 or y2 <= y1:
                logger.error(f"{self.task_id}--无效的区域设置: {region}, 图片尺寸: {img_width}x{img_height}")
                return False

            # 截取模板区域
            template = full_image[y1:y2, x1:x2]
            template_height, template_width = template.shape[:2]

            logger.debug(f"{self.task_id}--从原图截取模板区域: {region}, 模板尺寸: {template_width}x{template_height}")

            # 2. 获取当前屏幕截图并截取相同区域
            screenshot = self.d.screenshot(format='opencv')
            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            # 确保区域在屏幕截图范围内
            screen_height, screen_width = screenshot.shape[:2]
            x1_screen = max(0, min(x1, screen_width - 1))
            y1_screen = max(0, min(y1, screen_height - 1))
            x2_screen = max(x1_screen + 1, min(x2, screen_width))
            y2_screen = max(y1_screen + 1, min(y2, screen_height))

            if x2_screen <= x1_screen or y2_screen <= y1_screen:
                logger.error(f"{self.task_id}--区域超出屏幕范围: {region}, 屏幕尺寸: {screen_width}x{screen_height}")
                return False

            # 截取屏幕区域
            screen_region = screenshot[y1_screen:y2_screen, x1_screen:x2_screen]
            screen_region_height, screen_region_width = screen_region.shape[:2]

            logger.debug(
                f"{self.task_id}--从屏幕截取区域: {region}, 屏幕区域尺寸: {screen_region_width}x{screen_region_height}")

            # 3. 调整模板尺寸以匹配屏幕区域尺寸（如果需要）
            if template_width != screen_region_width or template_height != screen_region_height:
                logger.debug(f"{self.task_id}--调整模板尺寸以匹配屏幕区域")
                template = cv2.resize(template, (screen_region_width, screen_region_height),
                                      interpolation=cv2.INTER_AREA)
                template_height, template_width = template.shape[:2]
                logger.debug(f"{self.task_id}--模板调整后尺寸: {template_width}x{template_height}")

            # 4. 执行模板匹配
            result = cv2.matchTemplate(screen_region, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            similarity = max_val

            if debug:
                # 保存调试图像
                self._save_region_comparison_debug_image(
                    full_image, template, screenshot, screen_region,
                    region, similarity, min_similarity
                )

            # 5. 判断相似度是否达到阈值
            if similarity >= min_similarity:
                logger.debug(
                    f"{self.task_id}--区域相似度匹配成功: "
                    f"相似度 {similarity:.3f} >= 阈值 {min_similarity:.2f}, "
                    f"区域: {region}"
                )
                return True
            else:
                logger.debug(
                    f"{self.task_id}--区域相似度匹配失败: "
                    f"相似度 {similarity:.3f} < 阈值 {min_similarity:.2f}, "
                    f"区域: {region}"
                )
                return False

        except Exception as e:
            logger.error(f"{self.task_id}--区域相似度比较失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    def _save_region_comparison_debug_image(self, full_image, template, screenshot, screen_region,
                                            region, similarity, min_similarity):
        """保存区域比较的调试图像"""
        try:
            # 创建对比图像
            template_rgb = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            screen_region_rgb = cv2.cvtColor(screen_region, cv2.COLOR_BGR2RGB)

            # 调整图像大小以便对比显示
            max_height = 300
            scale_factor = max_height / max(template_rgb.shape[0], screen_region_rgb.shape[0])

            template_display = cv2.resize(template_rgb,
                                          (int(template_rgb.shape[1] * scale_factor),
                                           int(template_rgb.shape[0] * scale_factor)))
            screen_display = cv2.resize(screen_region_rgb,
                                        (int(screen_region_rgb.shape[1] * scale_factor),
                                         int(screen_region_rgb.shape[0] * scale_factor)))

            # 创建水平对比图
            if template_display.shape[0] != screen_display.shape[0]:
                # 调整高度一致
                max_h = max(template_display.shape[0], screen_display.shape[0])
                template_display = cv2.copyMakeBorder(template_display, 0, max_h - template_display.shape[0],
                                                      0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
                screen_display = cv2.copyMakeBorder(screen_display, 0, max_h - screen_display.shape[0],
                                                    0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))

            comparison = np.hstack([template_display, screen_display])

            # 添加文本信息
            text_lines = [
                f"Region: {region}",
                f"Similarity: {similarity:.3f}",
                f"Threshold: {min_similarity:.2f}",
                f"Result: {'PASS' if similarity >= min_similarity else 'FAIL'}"
            ]

            for i, text in enumerate(text_lines):
                cv2.putText(comparison, text, (10, 20 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(comparison, text, (10, 20 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # 添加标签
            label_y = comparison.shape[0] - 10
            cv2.putText(comparison, "Template", (10, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(comparison, "Screen Region",
                        (template_display.shape[1] + 10, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"region_comparison_{timestamp}.png")
            cv2.imwrite(debug_path, comparison)

            logger.debug(f"{self.task_id}--区域比较调试图像已保存: {debug_path}")

        except Exception as e:
            logger.warning(f"{self.task_id}--保存区域比较调试图像失败: {e}")

    def _handle_accidental_popups(self, accidental_processing: List[dict]) -> bool:
        """
        处理意外弹窗
        accidental_processing 格式示例:
        [
            {
                "popup_images": "/path/to/popup1.png",  # 单个图片路径
                "close_button": "/path/to/close_btn.png",
                "max_attempts": 2
            },
            {
                "popup_images": "/path/to/other_popup.png",
                "close_button": "/path/to/other_close.png",
                "max_attempts": 1
            }
        ]
        """
        try:
            if not accidental_processing:
                return False

            logger.debug(f"{self.task_id}--开始检查意外弹窗，共 {len(accidental_processing)} 种弹窗配置")

            # 遍历每种弹窗配置
            for popup_config in accidental_processing:
                popup_image = popup_config.get("popup_images")  # 单个图片路径
                close_button = popup_config.get("close_button")
                max_attempts = popup_config.get("max_attempts", 3)

                if not popup_image:
                    continue

                logger.debug(f"{self.task_id}--检查弹窗: {popup_image}，最多尝试 {max_attempts} 次")

                # 检查当前配置的弹窗
                for attempt in range(max_attempts):
                    popup_result = self.img_match(
                        image_data=popup_image,
                        min_similarity=0.7,
                        is_recursive_call=True  # 标记为递归调用
                    )

                    if popup_result:
                        logger.debug(
                            f"{self.task_id}--检测到弹窗: {popup_image}，相似度: {popup_result['similarity']:.2f}")

                        # 如果有关闭按钮，尝试点击关闭
                        if close_button:
                            if isinstance(close_button, list):
                                for i in close_button:
                                    close_result = self.img_match(
                                        image_data=i,
                                        min_similarity=0.7,
                                        is_recursive_call=True
                                    )
                                    if close_result:
                                        self.d.click(close_result["point"][0], close_result["point"][1])
                                        logger.warning(f"{self.task_id}--点击关闭按钮成功")
                                        time.sleep(1)  # 等待弹窗关闭
                                    else:
                                        logger.warning(f"{self.task_id}--检测到弹窗但未找到关闭按钮: {close_button}")
                            else:
                                close_result = self.img_match(
                                    image_data=close_button,
                                    min_similarity=0.7,
                                    is_recursive_call=True
                                )

                                if close_result:
                                    self.d.click(close_result["point"][0], close_result["point"][1])
                                    logger.warning(f"{self.task_id}--点击关闭按钮成功")
                                    time.sleep(1)  # 等待弹窗关闭
                                    return True
                                else:
                                    logger.warning(f"{self.task_id}--检测到弹窗但未找到关闭按钮: {close_button}")
                        time.sleep(1)
                        return True

                    # 如果当前配置没有检测到弹窗，直接跳出内层循环，检查下一个配置
                    logger.debug(f"{self.task_id}--未检测到弹窗: {popup_image}，尝试次数: {attempt + 1}")
                    break  # 跳出当前配置的尝试循环，检查下一个配置

            logger.debug(f"{self.task_id}--所有弹窗配置检查完毕，未检测到意外弹窗")
            return False

        except Exception as e:
            logger.error(f"{self.task_id}--处理意外弹窗时出错: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    def _log_debug_info(self, device_width, device_height, screenshot_width,
                        screenshot_height, template_width, template_height):
        """记录调试信息"""
        logger.debug(f"设备分辨率: {device_width}x{device_height}")
        logger.debug(f"截图尺寸: {screenshot_width}x{screenshot_height}")
        logger.debug(f"模板尺寸: {template_width}x{template_height}")
        logger.debug(f"缩放比例: x:{device_width / screenshot_width:.2f}, y:{device_height / screenshot_height:.2f}")

    def img_click(self, image_data: Union[str, np.ndarray, Image.Image],
                  min_similarity: float = 0.8, offset_x: int = 0,
                  offset_y: int = 0, debug: bool = False) -> bool:
        """图像匹配并点击"""
        try:
            sleep(1)  # 等待界面稳定
            result = self.img_match(image_data, min_similarity, debug)

            if not result:
                """
                operation: 操作描述
                error: 异常对象
                raise_error: 是否重新抛出异常
                """
                error_msg = f"{self.task_id}--{self.device}---{image_data}匹配失败"
                logger.error(error_msg)
                raise Exception(error_msg)
                # raise Exception(f"{self.task_id}--{self.device}---{image_data}图片匹配失败")
                # return False

            x, y = result["point"]
            target_x, target_y = x + offset_x, y + offset_y

            self.d.click(target_x, target_y)
            logger.warning(
                f"点击位置: ({target_x}, {target_y}) - {image_data if isinstance(image_data, str) else '图像'}")
            time.sleep(1.5)
            return True
        except Exception as e:
            self._handle_error(f"图片点击操作失败: {image_data}", e)
            return False

    def _save_debug_image(self, screenshot, top_left, bottom_right, center):
        """保存调试图像"""
        debug_img = screenshot.copy()

        # 绘制匹配区域和中心点
        cv2.rectangle(debug_img, top_left, bottom_right, (0, 0, 255), 2)
        cv2.drawMarker(debug_img, center, (0, 255, 0), cv2.MARKER_CROSS, 30, 2)

        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = os.path.join(self.debug_img, f"debug_match_{timestamp}.png")
        cv2.imwrite(debug_path, debug_img)
        self.last_debug_image = debug_path
        logger.debug(f"{self.task_id}--调试图像已保存: {debug_path}")

    def detect_color_in_region(self, target_color: Tuple[int, int, int],
                               region: Tuple[int, int, int, int] = None,
                               color_tolerance: int = 10,
                               min_pixel_count: int = 1,
                               debug: bool = False) -> Dict[str, Any]:
        """
        识别指定区域内的特定颜色

        Args:
            target_color: 目标颜色 (R, G, B)
            region: 识别区域 (x1, y1, x2, y2)，None表示全屏
            color_tolerance: 颜色容差范围
            min_pixel_count: 最小像素数量阈值
            debug: 是否调试模式

        Returns:
            Dict包含识别结果信息
        """
        try:
            # 获取屏幕截图
            screenshot = self.d.screenshot(format='opencv')

            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            # 如果指定了区域，则裁剪截图
            if region:
                x1, y1, x2, y2 = region
                # 确保区域在有效范围内
                height, width = screenshot.shape[:2]
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(x1 + 1, min(x2, width))
                y2 = max(y1 + 1, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    raise ValueError(f"无效的区域设置: {region}")

                region_screenshot = screenshot[y1:y2, x1:x2]
            else:
                region_screenshot = screenshot
                x1, y1 = 0, 0

            # 将BGR转换为RGB（OpenCV使用BGR，但输入是RGB）
            target_bgr = (target_color[2], target_color[1], target_color[0])

            # 定义颜色范围
            lower_bound = np.array([
                max(0, target_bgr[0] - color_tolerance),
                max(0, target_bgr[1] - color_tolerance),
                max(0, target_bgr[2] - color_tolerance)
            ])

            upper_bound = np.array([
                min(255, target_bgr[0] + color_tolerance),
                min(255, target_bgr[1] + color_tolerance),
                min(255, target_bgr[2] + color_tolerance)
            ])

            # 创建颜色掩码
            color_mask = cv2.inRange(region_screenshot, lower_bound, upper_bound)

            # 统计匹配的像素数量
            pixel_count = cv2.countNonZero(color_mask)

            # 获取匹配像素的坐标
            matches = cv2.findNonZero(color_mask)
            matched_coordinates = []

            if matches is not None:
                for match in matches:
                    x, y = match[0]
                    # 转换为全屏坐标
                    global_x = x + x1
                    global_y = y + y1
                    matched_coordinates.append((global_x, global_y))

            # 计算匹配比例
            total_pixels = region_screenshot.shape[0] * region_screenshot.shape[1]
            match_ratio = pixel_count / total_pixels if total_pixels > 0 else 0

            # 是否满足最小像素数量要求
            meets_threshold = pixel_count >= min_pixel_count

            result = {
                "pixel_count": pixel_count,
                "match_ratio": match_ratio,
                "meets_threshold": meets_threshold,
                "total_pixels_in_region": total_pixels,
                "matched_coordinates": matched_coordinates,
                "color_tolerance": color_tolerance,
                "target_color_rgb": target_color,
                "target_color_bgr": target_bgr,
                "region": region if region else (0, 0, screenshot.shape[1], screenshot.shape[0])
            }

            if debug:
                self._save_color_debug_image(
                    region_screenshot, color_mask, target_color,
                    pixel_count, region, x1, y1
                )

            logger.debug(
                f"{self.task_id}--颜色识别结果: "
                f"目标颜色RGB{target_color}, 匹配像素数: {pixel_count}, "
                f"匹配比例: {match_ratio:.4f}, 满足阈值: {meets_threshold}"
            )

            return result

        except Exception as e:
            self._handle_error(f"颜色识别失败", e, raise_error=False)
            return {
                "pixel_count": 0,
                "match_ratio": 0,
                "meets_threshold": False,
                "total_pixels_in_region": 0,
                "matched_coordinates": [],
                "color_tolerance": color_tolerance,
                "target_color_rgb": target_color,
                "error": str(e)
            }

    def _save_color_debug_image(self, screenshot, color_mask, target_color,
                                pixel_count, region, offset_x, offset_y):
        """保存颜色识别的调试图像"""
        try:
            # 创建调试图像
            debug_img = screenshot.copy()

            # 将掩码应用到原图（高亮显示匹配区域）
            highlighted = debug_img.copy()
            highlighted[color_mask > 0] = [0, 255, 0]  # 用绿色高亮匹配区域

            # 混合原图和高亮图
            alpha = 0.7
            debug_img = cv2.addWeighted(debug_img, 1 - alpha, highlighted, alpha, 0)

            # 添加文本信息
            text_lines = [
                f"Target RGB: {target_color}",
                f"Matched Pixels: {pixel_count}",
                f"Region: {region}" if region else "Full Screen"
            ]

            for i, text in enumerate(text_lines):
                cv2.putText(debug_img, text, (10, 30 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"color_detection_{timestamp}.png")
            cv2.imwrite(debug_path, debug_img)

            logger.debug(f"{self.task_id}--颜色识别调试图像已保存: {debug_path}")

        except Exception as e:
            logger.warning(f"{self.task_id}--保存颜色识别调试图像失败: {e}")

    def wait_for_color(self, target_color: Tuple[int, int, int],
                       region: Tuple[int, int, int, int] = None,
                       min_pixel_count: int = 1,
                       timeout: int = 3,
                       check_interval: float = 1.0) -> bool:
        """
        等待特定颜色出现

        Args:
            target_color: 目标颜色
            region: 识别区域
            min_pixel_count: 最小像素数量
            timeout: 超时时间（秒）
            check_interval: 检查间隔

        Returns:
            bool: 是否在超时前找到颜色
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.detect_color_in_region(
                target_color=target_color,
                region=region,
                min_pixel_count=min_pixel_count

            )

            if result["meets_threshold"]:
                logger.debug(f"{self.task_id}--在{time.time() - start_time:.1f}秒内找到目标颜色")
                return True

            sleep(check_interval)

        logger.debug(f"{self.task_id}--在{timeout}秒内未找到目标颜色")
        return False

    def safe_color_diff(actual, target):
        """安全计算颜色差异，避免整数溢出"""
        return abs(int(actual) - int(target))

    def check_point_color(self, point: Tuple[int, int],
                          target_color: Tuple[int, int, int],
                          color_tolerance: int = 5,
                          debug: bool = False) -> Union[Tuple[int, int], bool]:
        """
        检查指定点的颜色是否与目标颜色一致

        Args:
            point: 要检查的坐标点 (x, y)
            target_color: 目标颜色 (R, G, B)
            color_tolerance: 颜色容差范围
            debug: 是否调试模式

        Returns:
            如果颜色匹配返回坐标点 (x, y)，否则返回 False
        """
        try:
            # 获取屏幕截图
            screenshot = self.d.screenshot(format='opencv')

            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            height, width = screenshot.shape[:2]
            x, y = point

            # 检查坐标是否在有效范围内
            if x < 0 or x >= width or y < 0 or y >= height:
                logger.warning(f"{self.task_id}--坐标点({x}, {y})超出屏幕范围({width}x{height})")
                return False

            # 获取该点的颜色值 (BGR格式)
            pixel_color_bgr = screenshot[y, x]
            b, g, r = pixel_color_bgr

            # 将目标颜色转换为BGR
            target_bgr = (target_color[2], target_color[1], target_color[0])

            # 修复：使用安全的整数比较，避免溢出
            def safe_color_diff(actual, target):
                """安全计算颜色差异，避免整数溢出"""
                return abs(int(actual) - int(target))

            # 检查颜色是否在容差范围内（修复溢出问题）
            color_matches = (
                    safe_color_diff(r, target_color[0]) <= color_tolerance and
                    safe_color_diff(g, target_color[1]) <= color_tolerance and
                    safe_color_diff(b, target_color[2]) <= color_tolerance
            )

            # 计算总颜色差异（用于调试）
            color_diff = (
                    safe_color_diff(r, target_color[0]) +
                    safe_color_diff(g, target_color[1]) +
                    safe_color_diff(b, target_color[2])
            )

            if debug:
                self._save_point_color_debug_image(
                    screenshot, point, pixel_color_bgr, target_color,
                    color_matches, color_diff, color_tolerance
                )

            logger.debug(
                f"{self.task_id}--点颜色检查: 坐标({x}, {y}), "
                f"实际颜色RGB({r}, {g}, {b}), 目标颜色RGB{target_color}, "
                f"颜色差异: {color_diff}, 容差: {color_tolerance}, 匹配: {color_matches}"
            )

            if color_matches:
                return point  # 返回原始坐标点
            else:
                return False

        except Exception as e:
            self._handle_error(f"检查点颜色失败", e, raise_error=False)
            return False

    def _save_point_color_debug_image(self, screenshot, point, actual_color_bgr,
                                      target_color, color_matches, color_diff, tolerance):
        """保存点颜色检查的调试图像"""
        try:
            debug_img = screenshot.copy()
            x, y = point

            # 在点上绘制标记
            marker_color = (0, 255, 0) if color_matches else (0, 0, 255)  # 绿色匹配，红色不匹配
            cv2.drawMarker(debug_img, (x, y), marker_color, cv2.MARKER_CROSS, 20, 2)

            # 绘制一个圆圈突出显示点
            cv2.circle(debug_img, (x, y), 15, marker_color, 2)

            # 添加文本信息
            actual_rgb = (actual_color_bgr[2], actual_color_bgr[1], actual_color_bgr[0])
            target_rgb = target_color

            text_lines = [
                f"Point: ({x}, {y})",
                f"Actual: RGB{actual_rgb}",
                f"Target: RGB{target_rgb}",
                f"Diff: {color_diff}",
                f"Tolerance: {tolerance}",
                f"Match: {'Yes' if color_matches else 'No'}"  # 改为英文
            ]

            # 计算文本位置（确保在图像内）
            text_x = max(10, min(x - 100, screenshot.shape[1] - 300))
            text_y = max(100, min(y - 80, screenshot.shape[0] - len(text_lines) * 30))

            for i, text in enumerate(text_lines):
                cv2.putText(debug_img, text, (text_x, text_y + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(debug_img, text, (text_x, text_y + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.debug_img, f"point_color_check_{timestamp}.png")
            cv2.imwrite(debug_path, debug_img)

            logger.debug(f"{self.task_id}--点颜色检查调试图像已保存: {debug_path}")

        except Exception as e:
            logger.warning(f"{self.task_id}--保存点颜色检查调试图像失败: {e}")

    def wait_for_point_color(self, point: Tuple[int, int],
                             target_color: Tuple[int, int, int],
                             color_tolerance: int = 5,
                             timeout: int = 10,
                             check_interval: float = 1.0) -> Union[Tuple[int, int], bool]:
        """
        等待指定点的颜色变为目标颜色

        Args:
            point: 要检查的坐标点
            target_color: 目标颜色
            color_tolerance: 颜色容差
            timeout: 超时时间（秒）
            check_interval: 检查间隔

        Returns:
            超时前匹配成功返回坐标点，否则返回False
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.check_point_color(point, target_color, color_tolerance)

            if result:  # 如果返回坐标点（非False），说明匹配成功
                logger.debug(f"{self.task_id}--在{time.time() - start_time:.1f}秒内点颜色匹配成功")
                return result

            sleep(check_interval)

        logger.debug(f"{self.task_id}--在{timeout}秒内点颜色未匹配")
        return False

    def check_multiple_points_color(self, points: List[Tuple[int, int]],
                                    target_color: Tuple[int, int, int],
                                    color_tolerance: int = 5,
                                    require_all: bool = True) -> Dict[str, Any]:
        """
        检查多个点的颜色

        Args:
            points: 要检查的坐标点列表
            target_color: 目标颜色
            color_tolerance: 颜色容差
            require_all: 是否要求所有点都匹配

        Returns:
            包含检查结果的字典
        """
        results = {}
        matched_points = []
        unmatched_points = []

        for point in points:
            is_match = self.check_point_color(point, target_color, color_tolerance)

            if is_match:  # 返回坐标点表示匹配
                matched_points.append(point)
                results[str(point)] = True
            else:
                unmatched_points.append(point)
                results[str(point)] = False

        all_matched = len(matched_points) == len(points)
        any_matched = len(matched_points) > 0

        # 根据要求判断总体结果
        if require_all:
            overall_match = all_matched
        else:
            overall_match = any_matched

        return {
            "overall_match": overall_match,
            "all_matched": all_matched,
            "any_matched": any_matched,
            "matched_points": matched_points,
            "unmatched_points": unmatched_points,
            "matched_count": len(matched_points),
            "total_points": len(points),
            "detailed_results": results
        }

    def get_point_color(self, point: Tuple[int, int],
                        color_format: str = "RGB") -> Optional[Tuple[int, int, int]]:
        """
        获取指定坐标点的颜色值

        Args:
            point: 要获取颜色的坐标点 (x, y)
            color_format: 颜色格式 ("RGB" 或 "BGR")

        Returns:
            颜色值元组 (R, G, B) 或 (B, G, R)，失败返回None
        """
        try:
            # 获取屏幕截图
            screenshot = self.d.screenshot(format='opencv')

            if screenshot is None:
                raise Exception("无法获取屏幕截图")

            height, width = screenshot.shape[:2]
            x, y = point

            # 检查坐标是否在有效范围内
            if x < 0 or x >= width or y < 0 or y >= height:
                logger.warning(f"{self.task_id}--坐标点({x}, {y})超出屏幕范围({width}x{height})")
                return None

            # 获取该点的颜色值 (BGR格式)
            b, g, r = screenshot[y, x]

            if color_format.upper() == "RGB":
                color_value = (int(r), int(g), int(b))
            else:  # BGR格式
                color_value = (int(b), int(g), int(r))

            logger.debug(f"{self.task_id}--获取点颜色: 坐标({x}, {y}), {color_format}颜色值: {color_value}")

            return color_value

        except Exception as e:
            self._handle_error(f"获取点颜色失败", e, raise_error=False)
            return None

    def click_coordinate(self, x: int, y: int, duration: float= None,time_sleep: float = 2) -> None:
        """点击坐标"""
        if duration is None:
            self.d.click(x, y)
        else:
            self.d.long_click(x,y,duration=duration)
        logger.debug(f'{self.task_id}--点击坐标: ({x}, {y})')
        sleep(time_sleep)

    def app_screenshot(self, name: str, path: str = None, region: Tuple[int, int, int, int] = None) -> str:
        """截图并使用原子操作保存"""
        screenshot = self.d.screenshot()

        if region:
            screenshot = screenshot.crop(region)

        save_path = os.path.join(path if path else self.img_path, f"{name}.png")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 创建临时文件（自动管理生命周期）
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            temp_path = tmp_file.name

        try:
            # 保存到临时文件
            screenshot.save(temp_path, format='PNG')

            # 移动文件（原子操作）
            if os.path.exists(save_path):
                os.remove(save_path)
            shutil.move(temp_path, save_path)

            logger.warning(f'{self.task_id}--截图已保存: {save_path}')
            return save_path

        except Exception as e:
            logger.error(f'{self.task_id}--截图保存失败: {e}')
            return save_path
        finally:
            # 确保临时文件被清理
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def app_operations(self, operation: str, package_name: str, **kwargs) -> None:
        """应用操作通用方法"""
        operations = {
            'install': self.d.app_install,
            'uninstall': self.d.app_uninstall,
            'stop': self.d.app_stop,
            # 'stop_all': self.d.app_stop_all,
            'start': self.d.app_start
        }

        if operation not in operations:
            raise ValueError(f"{self.task_id}--不支持的操作用: {operation}")

        operations[operation](package_name, **kwargs)
        logger.debug(f'{self.task_id}--{operation}应用: {package_name}')

    def app_stop_all(self):
        self.d.app_stop_all()

    def error_screenshot(self, path):
        screenshot = self.d.screenshot()
        save_path = os.path.join(path, f"{self.task_id}_{self.device}.png")
        screenshot.save(save_path)
        logger.debug(f'{self.task_id}--错误截图已保存: {save_path}')