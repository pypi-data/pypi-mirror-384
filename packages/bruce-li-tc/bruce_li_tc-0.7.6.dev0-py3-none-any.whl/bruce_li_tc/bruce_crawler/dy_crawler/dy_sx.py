import random
import time
import threading
import logging
import re
import datetime
import tempfile
import shutil
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from threading import Lock
from loguru import logger

# 设置日志


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def parse_cookies(cookie_str):
    """解析Cookie字符串为字典列表"""
    cookies = []
    if not cookie_str:
        return cookies

    for pair in cookie_str.split(';'):
        if '=' in pair:
            key, value = pair.strip().split('=', 1)
            cookies.append({
                'name': key.strip(),
                'value': value.strip(),
                'domain': '.douyin.com',
                'path': '/',
            })
    return cookies


class DouyinPrivateSender:
    def __init__(self,
                 mode=2,
                 min_interval=10,
                 max_interval=40,
                 headless=False,
                 browser_path=None,
                 cookie=None,
                 login_method="cookie"):
        """
        初始化抖音私信发送器

        :param mode: 操作模式 (1: 单用户关闭整个浏览器, 2: 多标签页模式-每个用户后关闭标签页)
        :param min_interval: 最小操作间隔时间(秒)
        :param max_interval: 最大操作间隔时间(秒)
        :param headless: 是否使用无头模式
        :param browser_path: 浏览器路径
        :param cookie: Cookie字符串
        :param login_method: 登录方式 ("cookie" 或 "qrcode")
        """
        self.mode = mode
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.headless = headless
        self.browser_path = browser_path
        self.cookie = cookie
        self.login_method = login_method

        # 状态管理
        self.is_running = False
        self.is_paused = False
        self.pause_requested = False
        self.browser_closed = False  # 新增：# 标记浏览器是否已关闭
        self.lock = Lock()  # 新增：线程锁

        # 浏览器相关
        self.playwright = None
        self.browser = None
        self.context = None
        self.user_data_dir = None
        self.remake = "default"

        # 统计信息
        self.success_count = 0
        self.failure_count = 0
        self.current_task = None
        self.last_send_time = datetime.datetime.min

        # 回调函数
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None

    def set_callbacks(self, progress_cb=None, completion_cb=None, error_cb=None):
        """设置回调函数"""
        self.progress_callback = progress_cb
        self.completion_callback = completion_cb
        self.error_callback = error_cb

    def _create_user_data_dir(self):
        """创建临时用户数据目录"""
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.user_data_dir = Path(temp_dir) / f"dy_{self.remake}_{timestamp}"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[{self.remake}] 临时用户数据目录: {self.user_data_dir}")
        return self.user_data_dir

    def _setup_browser_context(self):
        """设置浏览器上下文"""
        self.playwright = sync_playwright().start()

        # 浏览器启动参数
        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-notifications",
                "--disable-save-password-bubble",
                "--disable-popup-blocking",
                "--start-maximized"
            ],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "timeout": 180000
        }

        if self.browser_path:
            launch_args["executable_path"] = self.browser_path

        if self.mode == 1:
            # 模式1：每个用户单独启动浏览器
            return None
        else:
            # 模式2：使用持久化上下文
            self._create_user_data_dir()
            context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                channel="chrome",
                **launch_args
            )
            """
            chrome版本
            139.0.7258.128(正式版本) (64位)
            默认路径在:C:/Users/<用户名>/AppData/Local/Google/Chrome/Application/chrome.exe
            自定义路径
            browser = p.chromium.launch(
                executable_path="D:/Chrome_Custom/chrome.exe",  # 自定义路径
                channel="chrome"  # 仍需声明渠道类型
            )
            """

            # 添加Cookie
            context.clear_cookies()
            if self.cookie and self.login_method == "cookie":
                cookies = parse_cookies(self.cookie)
                logger.info(f"[{self.remake}] 解析到 {len(cookies)} 个Cookie")
                context.add_cookies(cookies)

                # 验证关键Cookie是否存在
                all_cookies = context.cookies()
                session_cookie_exists = any(c['name'] == 'sessionid' for c in all_cookies)
                if not session_cookie_exists:
                    logger.warning(f"[{self.remake}] 关键Cookie (sessionid) 未找到，登录可能无效")
            else:
                logger.info(f"[{self.remake}] 未使用Cookie登录方式")

            self.context = context

            # 新增：监听浏览器关闭事件
            context.on("close", lambda: self._on_browser_closed())

            logger.info(f"[{self.remake}] 浏览器上下文已创建")
            return context

    def _on_browser_closed(self):
        """浏览器关闭时的回调函数"""
        with self.lock:
            self.browser_closed = True
            logger.warning(f"[{self.remake}] 浏览器已被手动关闭")

            # 停止任务
            if self.is_running:
                self.stop()

    def _is_browser_closed(self):
        """检查浏览器是否关闭"""
        with self.lock:
            return self.browser_closed
    def _login_with_qrcode(self, page):
        """二维码登录"""
        logger.info(f"[{self.remake}] 正在使用二维码登录...")
        page.goto("https://www.douyin.com/", timeout=60000)

        try:
            # 点击登录按钮
            login_btn = page.wait_for_selector('div[data-e2e="login-button"]', state="visible", timeout=10000)
            login_btn.click()
            logger.info(f"[{self.remake}] 已点击登录按钮")

            # 切换到二维码登录
            try:
                qrcode_tab = page.wait_for_selector('div.tab-item:has-text("扫码登录")', state="visible", timeout=5000)
                qrcode_tab.click()
                logger.info(f"[{self.remake}] 已切换到二维码登录")
            except:
                logger.info(f"[{self.remake}] 已经是二维码登录界面")

            # 等待二维码出现
            qrcode_img = page.wait_for_selector('div.qrcode-img img', state="visible", timeout=15000)
            logger.info(f"[{self.remake}] 二维码已显示，请扫码登录")

            # 等待登录成功
            page.wait_for_selector('div[data-e2e="user-info"]', state="visible", timeout=180000)
            logger.info(f"[{self.remake}] 扫码登录成功")
            return True

        except Exception as e:
            logger.error(f"[{self.remake}] 二维码登录失败: {str(e)}")
            return False

    def click_private_message_button(self, page, sec_uid):
        """点击私信按钮（带重试机制）"""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # 尝试多种定位策略
                selectors = [
                    'span:has-text("私信") >> visible=true',
                    'button:has-text("私信") >> visible=true',
                    'div[data-e2e="user-info"] button:has-text("私信")',
                    'xpath=//span[contains(text(), "私信")]/ancestor::button'
                ]

                for selector in selectors:
                    try:
                        private_btn = page.locator(selector)
                        if private_btn.count() > 0:
                            private_btn.first.scroll_into_view_if_needed()
                            private_btn.first.hover()
                            private_btn.first.click(delay=random.randint(50, 150))
                            logger.info(f"[{self.remake}] 已点击私信按钮 (尝试 #{attempt})")
                            return True
                    except Exception as e:
                        logger.debug(f"[{self.remake}] 选择器 {selector} 失败: {str(e)}")

                # 如果所有选择器都失败，刷新页面重试
                logger.warning(f"[{self.remake}] 未找到私信按钮，刷新页面重试 (尝试 #{attempt})")
                page.reload(timeout=30000)
                page.wait_for_load_state("networkidle", timeout=30000)

            except Exception as e:
                logger.warning(f"[{self.remake}] 点击私信按钮失败 (尝试 #{attempt}): {str(e)}")
                if attempt < max_retries:
                    page.wait_for_timeout(random.randint(1000, 3000))

        logger.error(f"[{self.remake}] 多次尝试后仍无法点击私信按钮")
        return False

    def send_private_message(self, sec_uid, message, remake=None):
        """
        发送私信给指定用户

        :param sec_uid: 目标用户的sec_uid
        :param message: 要发送的消息
        :param remake: 账号标识
        :return: 发送是否成功
        """
        if remake:
            self.remake = sanitize_filename(remake)

        context = None
        page = None

        try:
            # 模式1：每个用户单独启动浏览器
            if self.mode == 1:
                self._create_user_data_dir()
                self.playwright = sync_playwright().start()

                # 浏览器启动参数
                launch_args = {
                    "headless": self.headless,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--disable-notifications",
                        "--disable-save-password-bubble",
                        "--disable-popup-blocking",
                        "--start-maximized"
                    ],
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "timeout": 180000
                }

                if self.browser_path:
                    launch_args["executable_path"] = self.browser_path

                context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    channel="chrome",
                    **launch_args
                )

                # 添加Cookie
                context.clear_cookies()
                if self.cookie and self.login_method == "cookie":
                    cookies = parse_cookies(self.cookie)
                    context.add_cookies(cookies)

            # 模式2：使用已存在的浏览器上下文
            else:
                if not self.context:
                    self.context = self._setup_browser_context()
                context = self.context

            # 创建新页面
            page = context.new_page()

            # 登录检查
            if self.login_method == "qrcode":
                if not self._login_with_qrcode(page):
                    return False

            # 直接导航至目标用户主页
            logger.info(f"[{self.remake}] 访问用户主页：https://www.douyin.com/user/{sec_uid}")
            page.goto(f"https://www.douyin.com/user/{sec_uid}", timeout=60000)

            # 处理可能出现的保存登录信息弹窗
            try:
                save_btn = page.wait_for_selector("text=保存", state="visible", timeout=3000)
                save_btn.click(timeout=2000)
                logger.info(f"[{self.remake}] 已处理保存登录信息弹窗")
            except:
                logger.info(f"[{self.remake}] 保存登录信息弹窗未出现")

            # 等待用户信息加载完成
            page.wait_for_selector('div[data-e2e="user-info"]', state="visible", timeout=60000)
            logger.info(f"[{self.remake}] 用户主页加载完成")

            # 定位并点击私信按钮（带重试机制）
            if not self.click_private_message_button(page, sec_uid):
                logger.error(f"[{self.remake}] 无法点击私信按钮，跳过此用户")
                return False

            # 等待私信对话框完全加载
            logger.info(f"[{self.remake}] 等待私信对话框加载...")
            try:
                # 使用更可靠的等待条件
                page.wait_for_selector('div.notranslate.public-DraftEditor-content', state="visible", timeout=30000)
                logger.info(f"[{self.remake}] 私信对话框已加载")
            except PlaywrightTimeoutError:
                logger.warning(f"[{self.remake}] 私信对话框加载超时，尝试重新点击私信按钮")
                if not self.click_private_message_button(page, sec_uid):
                    logger.error(f"[{self.remake}] 第二次尝试仍无法打开私信对话框")
                    return False
                page.wait_for_selector('div.notranslate.public-DraftEditor-content', state="visible", timeout=30000)

            # 点击输入框激活编辑状态
            input_div = page.locator('div.notranslate.public-DraftEditor-content')
            input_div.click()
            logger.info(f"[{self.remake}] 已点击输入框")

            # 使用键盘输入消息
            logger.info(f"[{self.remake}] 正在输入消息: {message}")
            for char in message:
                page.keyboard.type(char, delay=random.randint(50, 150))
            logger.info(f"[{self.remake}] 消息输入完成")

            # 定位并点击发送按钮
            send_btn = page.locator('span.PygT7Ced.e2e-send-msg-btn')
            send_btn.wait_for(state="visible", timeout=30000)
            send_btn.hover()
            send_btn.click()
            logger.info(f"[{self.remake}] 已点击发送按钮")

            # 验证消息发送成功
            try:
                # 等待发送状态变化
                send_btn.wait_for(state="detached", timeout=10000)
                logger.info(f"[{self.remake}] 消息发送成功")
            except:
                # 检查消息是否出现在聊天记录中
                try:
                    partial_msg = message[:10] + "..." if len(message) > 10 else message
                    page.wait_for_selector(f'div.chat-message-content:has-text("{partial_msg}")',
                                           state="visible", timeout=5000)
                    logger.info(f"[{self.remake}] 消息发送成功（通过聊天记录验证）")
                except:
                    logger.warning(f"[{self.remake}] 发送状态验证失败，但可能已发送成功")

            # 关闭对话框
            try:
                close_btn = page.locator('button[aria-label="关闭"]')
                close_btn.click(timeout=2000)
                logger.info(f"[{self.remake}] 已关闭对话框")
            except:
                pass

            # 统计成功
            self.success_count += 1
            self.last_send_time = datetime.datetime.now()
            logger.info(f"[{self.remake}] 消息发送成功! 总成功: {self.success_count} 条")

            return True

        except Exception as e:
            logger.error(f"[{self.remake}] 操作失败: {str(e)}", exc_info=True)
            if page:
                error_file = f"{self.remake}_error_{sec_uid}.png"
                page.screenshot(path=error_file)
                logger.info(f"[{self.remake}] 错误截图已保存: {error_file}")

            if self.error_callback:
                self.error_callback(self.remake, sec_uid, str(e))

            self.failure_count += 1
            logger.warning(f"[{self.remake}] 总失败: {self.failure_count} 条")
            return False

        finally:
            # 无论成功与否，都关闭当前标签页
            try:
                if page:
                    page.close()
                    logger.info(f"[{self.remake}] 标签页已关闭")
            except Exception as e:
                logger.error(f"[{self.remake}] 关闭标签页时出错: {str(e)}")

            # 模式1：关闭整个浏览器
            if self.mode == 1:
                try:
                    if context:
                        context.close()
                    if self.playwright:
                        self.playwright.stop()
                    logger.info(f"[{self.remake}] 浏览器已关闭")
                except Exception as e:
                    logger.error(f"[{self.remake}] 关闭浏览器时出错: {str(e)}")

                # 清理临时目录
                try:
                    if self.user_data_dir:
                        shutil.rmtree(self.user_data_dir)
                        logger.info(f"[{self.remake}] 已清理临时目录")
                except Exception as e:
                    logger.error(f"[{self.remake}] 清理临时目录失败: {str(e)}")

    def send_batch(self, user_list, message, remake=None, limit=None):
        """
        批量发送私信

        :param user_list: 用户sec_uid列表
        :param message: 要发送的消息
        :param remake: 账号标识
        :param limit: 发送数量限制
        """
        if self.is_running:
            logger.warning(f"[{self.remake}] 任务正在进行中，请先停止当前任务")
            return

        self.is_running = True
        self.is_paused = False
        self.pause_requested = False

        if remake:
            self.remake = sanitize_filename(remake)

        # 应用发送限制
        if limit is not None and limit > 0:
            user_list = user_list[:limit]

        total = len(user_list)
        self.success_count = 0
        self.failure_count = 0

        logger.info(f"[{self.remake}] 开始批量发送，总数: {total} 条")

        # 模式2：提前初始化浏览器上下文
        if self.mode == 2:
            self._setup_browser_context()

        for index, sec_uid in enumerate(user_list):
            # 检查浏览器是否关闭（关键修改）
            if self._is_browser_closed():
                logger.warning(f"[{self.remake}] 浏览器已被关闭，停止发送")
                break


            if not self.is_running or self.pause_requested:
                break

            # 检查暂停状态
            while self.is_paused:
                time.sleep(0.5)
                if not self.is_running or self.pause_requested:
                    break

            if not self.is_running or self.pause_requested:
                break

            # 记录当前任务
            self.current_task = sec_uid

            # 发送消息
            try:
                success = self.send_private_message(sec_uid, message, self.remake)
            except Exception as e:
                logger.error(f"[{self.remake}] 发送异常: {str(e)}")
                success = False

            # 更新进度
            if self.progress_callback:
                self.progress_callback(
                    index + 1,
                    total,
                    sec_uid,
                    success,
                    self.success_count,
                    self.failure_count
                )

            # 随机间隔（最后一个不等待）
            if index < total - 1:
                interval = random.randint(self.min_interval, self.max_interval)
                logger.info(f"[{self.remake}] 等待 {interval} 秒后继续...")

                # 在等待期间检查暂停和浏览器关闭状态
                start_time = time.time()
                while time.time() - start_time < interval:
                    if not self.is_running or self.pause_requested or self._is_browser_closed():
                        break
                    time.sleep(0.5)

        # 任务完成或停止
        self.is_running = False
        self.current_task = None

        # 模式2：关闭浏览器
        if self.mode == 2:
            try:
                if self.context:
                    self.context.close()
                if self.playwright:
                    self.playwright.stop()
                logger.info(f"[{self.remake}] 浏览器已关闭")
            except Exception as e:
                logger.error(f"[{self.remake}] 关闭浏览器时出错: {str(e)}")

            # 清理临时目录
            try:
                if self.user_data_dir:
                    shutil.rmtree(self.user_data_dir)
                    logger.info(f"[{self.remake}] 已清理临时目录")
            except Exception as e:
                logger.error(f"[{self.remake}] 清理临时目录失败: {str(e)}")

        # 触发完成回调
        if self.completion_callback:
            self.completion_callback(
                self.remake,
                self.success_count,
                self.failure_count,
                self.pause_requested
            )

        logger.info(f"[{self.remake}] 批量发送完成. 成功: {self.success_count}, 失败: {self.failure_count}")

    def start(self, user_list, message, remake=None, limit=None):
        """启动发送任务（在新线程中）"""
        if self.is_running:
            return False

        self.thread = threading.Thread(
            target=self.send_batch,
            args=(user_list, message, remake, limit),
            name=f"Sender-{remake or 'default'}"
        )
        self.thread.daemon = True  # 设置为守护线程
        self.thread.start()
        return True

    def pause(self):
        """暂停发送"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            logger.info(f"[{self.remake}] 发送已暂停")
            return True
        return False

    def resume(self):
        """恢复发送"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            logger.info(f"[{self.remake}] 发送已恢复")
            return True
        return False

    def stop(self):
        """停止发送并关闭所有资源"""
        if self.is_running:
            self.pause_requested = True
            self.is_running = False

            # 强制关闭浏览器
            try:
                if self.context:
                    self.context.close()
                    self.context = None
                if self.playwright:
                    self.playwright.stop()
                    self.playwright = None
                logger.info(f"[{self.remake}] 浏览器已强制关闭")
            except Exception as e:
                logger.error(f"[{self.remake}] 强制关闭浏览器时出错: {str(e)}")

            # 清理临时目录
            try:
                if self.user_data_dir:
                    shutil.rmtree(self.user_data_dir, ignore_errors=True)
                    logger.info(f"[{self.remake}] 已清理临时目录")
                    self.user_data_dir = None
            except Exception as e:
                logger.error(f"[{self.remake}] 清理临时目录失败: {str(e)}")

            # 确保线程停止
            if hasattr(self, 'thread') and self.thread.is_alive():
                try:
                    self.thread.join(3.0)  # 等待线程结束，最多3秒
                except:
                    pass

            logger.info(f"[{self.remake}] 发送已停止")
            return True
        return False

    def clean_temp_directories(self, prefix="dy_", base_dir=None):
        """清理临时目录"""
        base_path = Path(base_dir) if base_dir else Path(os.getenv("TEMP", "/tmp"))
        logging.info(f"扫描目录: {base_path}")

        deleted_count = 0
        error_count = 0
        for dir_path in base_path.iterdir():
            if not dir_path.is_dir() or not dir_path.name.startswith(prefix):
                continue

            try:
                shutil.rmtree(dir_path)
                logging.info(f"已删除: {dir_path.name}")
                deleted_count += 1
            except Exception as e:
                logging.error(f"删除失败 [{dir_path.name}]: {str(e)}")
                error_count += 1

        logging.info(f"清理完成: 删除 {deleted_count} 个目录, 失败 {error_count} 个")


"""
from douyin_private_sender import DouyinPrivateSender
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 回调函数定义
def progress_callback(current, total, sec_uid, success, success_count, failure_count):
    status = "成功" if success else "失败"
    logging.info(f"进度: {current}/{total} | 用户: {sec_uid} | 状态: {status}")
    logging.info(f"统计: 成功 {success_count} 条, 失败 {failure_count} 条")

def completion_callback(remake, success_count, failure_count, paused):
    status = "暂停" if paused else "完成"
    logging.info(f"任务{status} | 账号: {remake}")
    logging.info(f"最终统计: 成功 {success_count} 条, 失败 {failure_count} 条")

def error_callback(remake, sec_uid, error):
    logging.error(f"发送失败 | 账号: {remake} | 用户: {sec_uid}")
    logging.error(f"错误信息: {error}")

# 主函数
def main():
    # 抖音账号配置
    ACCOUNTS = [
        {
            "name": "账号1",
            "cookie": "sessionid=your_session_id_here; other_cookie=value",
            "message": "您好，这是来自账号1的测试消息"
        },
        {
            "name": "账号2",
            "cookie": "sessionid=another_session_id; other_cookie=value",
            "message": "您好，这是来自账号2的测试消息"
        }
    ]
    
    # 目标用户列表
    USER_LIST = [
        "MS4wLjABAAAAv7i5uK_r2q7H4XJ0YyCQY2X3XbK3X9XZ",
        "MS4wLjABAAAAx9x9x9x9x9x9x9x9x9x9",
        "MS4wLjABAAAAy8y8y8y8y8y8y8y8y8y8"
    ]
    
    # 创建发送器实例
    senders = []
    for account in ACCOUNTS:
        sender = DouyinPrivateSender(
            mode=2,  # 使用多标签页模式
            min_interval=15,
            max_interval=30,
            headless=False,  # 显示浏览器
            cookie=account["cookie"],
            login_method="cookie"
        )
        sender.set_callbacks(
            progress_cb=progress_callback,
            completion_cb=completion_callback,
            error_cb=error_callback
        )
        senders.append(sender)
    
    # 启动发送任务
    for idx, sender in enumerate(senders):
        account = ACCOUNTS[idx]
        sender.start(
            user_list=USER_LIST,
            message=account["message"],
            remake=account["name"],
            limit=2  # 每个账号发送2条
        )
    
    # 主循环监控任务状态
    try:
        while any(sender.is_running for sender in senders):
            # 这里可以添加控制逻辑，例如：
            # if some_condition:
            #     senders[0].pause()
            # elif other_condition:
            #     senders[0].resume()
            
            time.sleep(1)
            print("任务运行中...")
            
    except KeyboardInterrupt:
        print("检测到中断信号，停止所有任务...")
        for sender in senders:
            sender.stop()
    
    print("所有任务已结束")

if __name__ == "__main__":
    main()
"""