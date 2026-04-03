"""
豆包网页版自动化采集器
使用 Selenium 自动化 Chrome 浏览器，自动遍历所有会话并请求 AI 总结
严格按照流程执行，元素定位使用多策略兼容，鲁棒性强
支持：https://www.doubao.com

流程：
1. 启动 Chrome，打开 doubao.com
2. 等待用户手动登录，按回车继续
3. 进入左侧【历史会话列表】
4. 遍历每一个会话，依次执行：
   a. 进入会话
   b. 定位输入框，输入总结请求
   c. 定位发送按钮并发送
   d. 等待 AI 回复完成
   e. 提取最后一条消息
   f. 提取日期时间、提取总结内容
   g. 保存会话标题、日期、总结
   h. 返回会话列表
5. 所有会话处理完后：
   a. 按日期分组
   b. 生成清晰的日报
   c. 输出到控制台
   d. 保存到 doubao_daily_report.md
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import json
import re

from .base import BaseCollector, SessionData, Message, register_collector

logger = logging.getLogger(__name__)


@register_collector
class DoubaoSeleniumCollector(BaseCollector):
    name = "doubao_selenium"
    version = "3.0.0"
    priority = 51

    def get_data_path(self) -> Path:
        return Path("./doubao_web")

    def validate(self) -> bool:
        return True

    def __init__(self):
        self.driver = None
        self.wait = None

    def get_browser_options(self):
        from selenium.webdriver.chrome.options import Options
        from pathlib import Path

        options = Options()
        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        # 使用持久化的用户数据目录，保持登录状态，不需要每次登录
        # 独立目录不影响用户主浏览器，复用这个目录保持登录状态
        chrome_profile = Path("./.doubao-chrome-profile")
        chrome_profile.mkdir(exist_ok=True)
        options.add_argument(f"--user-data-dir={str(chrome_profile.absolute())}")

        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--remote-debugging-port=9222")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def _init_driver(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait

        # 如果已有driver，先关闭
        if self.driver is not None:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.wait = None

        logger.info("正在初始化Chrome驱动...")
        options = self.get_browser_options()
        # Selenium 4+ 自带 Selenium Manager，自动下载匹配版本的 chromedriver
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)
        logger.info(f"Chrome驱动初始化完成，当前URL: {self.driver.current_url}")
        
        # 先打开首页，有时候直接打开列表会被重定向
        logger.info("打开豆包首页...")
        self.driver.get("https://www.doubao.com/")
        time.sleep(3)
        
        # 直接访问历史列表页面
        logger.info("导航到历史列表页面...")
        self.driver.get("https://www.doubao.com/chat/thread/list")
        time.sleep(5)

        # 确认已经在历史列表页面
        current_url = self.driver.current_url
        logger.info(f"_init_driver 完成，当前URL: {current_url}")
        if "thread/list" in current_url:
            logger.info("✅ 已直接打开历史列表页面")
        else:
            logger.warning(f"⚠️  当前不在历史列表页面，URL: {current_url}")
            # 如果跳转失败，尝试点击历史按钮
            try:
                history_selectors = [
                    "//*[contains(text(), '历史')]",
                    "//*[contains(text(), '历史对话')]",
                    "[class*='history']",
                    "a[href*='history']",
                    "a[href*='thread/list']"
                ]
                from selenium.webdriver.common.by import By
                found = False
                for selector in history_selectors:
                    try:
                        if selector.startswith("//"):
                            elements = self.driver.find_elements(By.XPATH, selector)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                logger.info(f"找到历史按钮，点击: {selector}")
                                elem.click()
                                time.sleep(2)
                                found = True
                                break
                        if found:
                            break
                    except Exception as e:
                        logger.debug(f"尝试selector {selector} 失败: {e}")
                        continue
                if found:
                    logger.info("重新初始化后已点击历史会话按钮")
                    current_url = self.driver.current_url
                    logger.info(f"点击后当前URL: {current_url}")
            except Exception as e:
                logger.error(f"点击历史按钮失败: {e}")
        time.sleep(3)

    def collect(self, target_date: date) -> List[SessionData]:
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError:
            logger.error("selenium 未安装：pip install selenium webdriver-manager")
            return []

        logger.info(f"[{self.name}] 开始采集")

        try:
            self._init_driver()

            # 检测是否已经登录并打开历史列表
            from selenium.webdriver.common.by import By
            current_url = self.driver.current_url
            already_ok = False
            
            # 如果已经在历史列表页面，并且能看到会话列表，说明已经登录OK
            if "thread/list" in current_url:
                # 尝试查找会话元素
                sessions_check = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='thread_detail_item']")
                if sessions_check and len(sessions_check) > 0 and sessions_check[0].is_displayed():
                    logger.info("✅ 已检测到登录状态，历史列表已加载，无需手动确认")
                    already_ok = True
            
            if not already_ok:
                print("\n👉 请在浏览器中登录豆包，登录完成后按回车继续...")
                input()
            # 重新导航到历史列表页面确保位置正确
            logger.info("导航到历史列表页面...")
            self.driver.get("https://www.doubao.com/chat/thread/list")
            time.sleep(5)

            # 确认已经在历史列表页面
            current_url = self.driver.current_url
            logger.info(f"collect 方法 - 当前URL: {current_url}")
            if "thread/list" in current_url:
                logger.info("✅ 已成功打开历史列表页面")
            else:
                logger.warning(f"⚠️  仍不在历史列表页面，当前URL: {current_url}")
                # 如果跳转失败，尝试点击历史按钮
                try:
                    history_selectors = [
                        "//*[contains(text(), '历史')]",
                        "//*[contains(text(), '历史对话')]",
                        "[class*='history']",
                        "a[href*='history']",
                        "a[href*='thread/list']"
                    ]
                    from selenium.webdriver.common.by import By
                    found = False
                    for selector in history_selectors:
                        try:
                            if selector.startswith("//"):
                                elements = self.driver.find_elements(By.XPATH, selector)
                            else:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                if elem.is_displayed():
                                    logger.info(f"找到历史按钮，点击: {selector}")
                                    elem.click()
                                    time.sleep(2)
                                    logger.info("已点击历史会话按钮")
                                    found = True
                                    break
                            if found:
                                break
                        except:
                            continue
                except:
                    pass

            sessions = self._get_session_list()
            logger.info(f"找到 {len(sessions)} 个会话")

            # 如果还是找不到，让用户确认一下
            if not sessions:
                print("\n⚠️  没有找到历史会话，请确认：")
                print("   1. 登录成功后，左侧历史会话列表是否已经展开？")
                print("   2. 你确实有历史对话会话吗？")
                print("按回车继续...")
                input()
                # 再试一次
                sessions = self._get_session_list()
                logger.info(f"重新找找到 {len(sessions)} 个会话")

            # 加载缓存，跳过已处理过的会话
            cache_dir = Path("./.doubao-cache")
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / "processed_sessions.json"
            processed_titles = set()
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        processed_titles = set(json.load(f))
                    logger.info(f"加载缓存：已处理过 {len(processed_titles)} 个会话")
                except:
                    pass

            results = []
            for sess in sessions:
                title = sess["title"]
                if title in processed_titles:
                    logger.info(f"⏭️  跳过已处理：{title}")
                    # 从缓存加载
                    cached_file = cache_dir / f"{self._hash_title(title)}.json"
                    if cached_file.exists():
                        try:
                            with open(cached_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                cached_session = SessionData(
                                    session_id=data["session_id"],
                                    source=data["source"],
                                    title=data["title"],
                                    summary=data["summary"],
                                    start_time=datetime.fromisoformat(data["start_time"])
                                )
                                results.append(cached_session)
                                logger.info(f"📦 从缓存加载：{title}")
                        except:
                            logger.warning(f"⚠️  缓存加载失败，重新处理：{title}")
                    continue
                
                try:
                    res = self._process_single_session(sess)
                    if res:
                        results.append(res)
                        # 保存到缓存
                        cached_data = {
                            "session_id": res.session_id,
                            "source": res.source,
                            "title": res.title,
                            "summary": res.summary,
                            "start_time": res.start_time.isoformat()
                        }
                        cached_file = cache_dir / f"{self._hash_title(title)}.json"
                        with open(cached_file, "w", encoding="utf-8") as f:
                            json.dump(cached_data, f, ensure_ascii=False, indent=2)
                        processed_titles.add(title)
                        # 更新缓存索引
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(list(processed_titles), f, ensure_ascii=False)
                        logger.info(f"✅ 处理完成：{res.title}")
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"❌ 处理失败：{error_msg}")
                    # 如果是session失效或窗口关闭，重新初始化driver
                    if "invalid session id" in error_msg or "no such window" in error_msg or "stale element reference" in error_msg:
                        logger.warning("检测到会话失效/窗口关闭，正在重新初始化Chrome驱动...")
                        try:
                            self._init_driver()
                            logger.info("Chrome驱动重新初始化完成，继续处理")
                        except Exception as init_e:
                            logger.error(f"重新初始化失败: {init_e}")

            if results:
                # 按日期过滤，只保留目标日期的会话
                target_results = [
                    sess for sess in results
                    if sess.start_time.date() == target_date
                ]
                logger.info(f"目标日期 {target_date} 匹配到 {len(target_results)} 个会话")
                self._generate_daily_report(results)
                return target_results

            return []

        except Exception as e:
            logger.error(f"采集失败：{e}")
            return []

    def _get_session_list(self) -> List[Dict]:
        time.sleep(4)
        sessions = []
        found = set()

        from selenium.webdriver.common.by import By

        # 尝试滚动加载更多历史会话
        try:
            # 找到历史会话容器并滚动到底部加载更多
            history_containers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='scroll_view'], [data-testid='thread_list_all'], div.scrollable-Se7zNt, [class*='history'], [class*='sidebar'], nav, aside")
            for container in history_containers:
                if container.is_displayed():
                    # 滚动几次加载更多
                    for _ in range(5):
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                        time.sleep(1)
                    break
        except:
            pass

        # 打印页面信息帮助调试
        logger.debug(f"页面标题: {self.driver.title}")
        logger.debug(f"当前URL: {self.driver.current_url}")

        # 尝试多种选择器，适应不同的豆包页面结构
        selectors = [
            "[data-testid='thread_detail_item']",
            "div.thread-item-fq1YON",
            "div[class*='thread-item']",
            "div[class*='sidebar'] div[class*='item']",
            "div[class*='history'] div[class*='item']",
            "div[class*='history'] [role='listitem']",
            ".side-bar-item",
            ".history-item",
            ".thread-item",
            ".session-item",
            "[class*='conversation']",
            "[class*='chat']",
            "[class*='item']",
            "div[role='button']",
            "a[href*='/chat/']",
            "li div",
            "nav li",
            "aside li",
            ".sidebar li",
            ".history li"
        ]

        for s in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, s)
                logger.debug(f"选择器 '{s}' 找到 {len(elements)} 个元素")
                for idx, e in enumerate(elements):
                    try:
                        if not e.is_displayed():
                            continue
                        
                        # 对于新的页面结构，尝试从内部专门的title元素提取标题
                        title = None
                        data_id = None
                        try:
                            title_elem = e.find_element(By.CSS_SELECTOR, "[data-testid='thread_detail_item_title']")
                            if title_elem and title_elem.is_displayed():
                                title = title_elem.text.strip()
                        except:
                            pass
                        
                        # 尝试获取data-id属性
                        try:
                            data_id = e.get_attribute("data-id")
                        except:
                            pass
                        
                        # 如果没找到专门的title元素，使用整个元素文本
                        if not title:
                            title = e.text.strip()
                            # 如果包含换行，只取第一行作为标题
                            if '\n' in title:
                                title = title.split('\n')[0].strip()
                        
                        if not title or len(title) < 2 or title in found:
                            continue
                        # 过滤掉明显不是会话标题的内容
                        if any(kw in title for kw in {"新对话", "云盘", "更多", "历史对话", "推荐", "空间", "我的", "登录", "注册", "发现", "通知", "打开对话"}):
                            continue
                        if len(title) > 50:  # 太长的可能不是标题
                            continue
                        found.add(title)
                        # 不保存元素引用，只保存索引和data-id，点击时重新获取
                        sessions.append({"title": title, "index": len(sessions), "data_id": data_id, "selector": s})
                    except:
                        continue
            except Exception as e:
                logger.debug(f"选择器 '{s}' 出错: {e}")
                continue

        # 如果还没找到，尝试获取整个页面中所有可见的元素，只要有短文本都认为可能是会话
        if not sessions:
            try:
                logger.debug("尝试回退策略：获取页面所有元素")
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, "div, li, a, button")
                for idx, e in enumerate(all_elements):
                    try:
                        if not e.is_displayed():
                            continue
                        title = e.text.strip()
                        if not title or len(title) < 2 or len(title) > 50 or title in found:
                            continue
                        if any(kw in title for kw in {"新对话", "云盘", "更多", "历史对话", "推荐", "空间", "我的", "登录", "注册", "发现", "通知", "打开对话"}):
                            continue
                        found.add(title)
                        sessions.append({"title": title, "index": len(sessions), "data_id": None, "selector": "div, li, a, button"})
                    except:
                        continue
            except:
                pass

        # 去重
        logger.info(f"最终找到 {len(sessions)} 个唯一会话")
        return sessions

    def _process_single_session(self, sess) -> Optional[SessionData]:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        try:
            logger.info(f"开始处理会话: {sess['title']}")
            
            # 回到历史列表页面，重新查找这个会话元素
            # 因为之前页面导航后，原来的元素引用已经失效
            if "thread/list" not in self.driver.current_url:
                self.driver.get("https://www.doubao.com/chat/thread/list")
                time.sleep(3)
                # 重新滚动加载
                try:
                    history_containers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='scroll_view'], [data-testid='thread_list_all']")
                    for container in history_containers:
                        if container.is_displayed():
                            for _ in range(3):
                                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                                time.sleep(0.5)
                            break
                except:
                    pass
                time.sleep(2)
            
            # 重新查找会话元素
            element = None
            if sess.get("data_id"):
                # 如果有data-id，直接按属性查找
                try:
                    selector = f"[data-id='{sess['data_id']}']"
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for e in elements:
                        if e.is_displayed():
                            element = e
                            break
                except:
                    pass
            
            if element is None:
                # 按选择器和索引查找
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, sess["selector"])
                    visible_elements = [e for e in elements if e.is_displayed()]
                    # 过滤掉被过滤掉的标题，找到对应索引的可见元素
                    if sess["index"] < len(visible_elements):
                        element = visible_elements[sess["index"]]
                    else:
                        # 如果索引不对，遍历找标题匹配的
                        for e in elements:
                            try:
                                title_candidate = None
                                title_elem = e.find_element(By.CSS_SELECTOR, "[data-testid='thread_detail_item_title']")
                                if title_elem:
                                    title_candidate = title_elem.text.strip()
                                if not title_candidate:
                                    title_candidate = e.text.strip().split('\n')[0].strip()
                                if title_candidate == sess["title"]:
                                    element = e
                                    break
                            except:
                                continue
                except:
                    pass
            
            if element is None:
                logger.warning(f"无法找到会话元素: {sess['title']}，跳过")
                return None
            
            element.click()
            time.sleep(4)

            # 多个口语化提示词，随机选择一个，避免被机器识别
            prompts = [
                "帮我完整总结一下我们这段对话，把所有问题、回答和重点都涵盖进去，最后告诉我这个对话是什么时候开始的，格式要像这样：YYYY-MM-DD HH:MM",
                "麻烦你总结一下咱们这个多轮聊天，包括我问了啥你答了啥，关键内容别落下，另外麻烦告诉我这个对话开始的具体时间，用 YYYY-MM-DD HH:MM 这个格式就行",
                "请帮我把这段对话做个完整总结，内容要覆盖所有问题和回答，把要点都提炼出来，最后请给我对话开始的日期时间，格式为 YYYY-MM-DD HH:MM",
                "你能帮我整理一下这段对话吗？把所有讨论内容、问题答案都总结一下，记一下关键点，最后麻烦说一下这个对话是什么时候开始的，按这个格式：YYYY-MM-DD HH:MM",
                "帮我梳理一下我们这次多轮交流，总结清楚所有提问、回答和核心观点，特别需要你告诉我这段对话开始的具体时间，格式请用 YYYY-MM-DD HH:MM"
            ]
            import random
            prompt = random.choice(prompts)

            inp = None
            for sel in [
                "[data-testid='chat_input_input']",
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='发送']",
                "[role='textbox']",
                "footer textarea"
            ]:
                es = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for e in es:
                    if e.is_displayed():
                        inp = e
                        break
                if inp:
                    break

            if not inp:
                logger.warning("未找到输入框，跳过该会话")
                # 尝试返回
                try:
                    self.driver.back()
                    time.sleep(3)
                except:
                    pass
                return None

            logger.info(f"找到输入框，发送提示词：{prompt[:30]}...")
            inp.click()
            time.sleep(0.5)
            inp.send_keys(Keys.COMMAND + "a")
            inp.send_keys(Keys.DELETE)
            time.sleep(0.5)
            inp.send_keys(prompt)
            time.sleep(1)

            # 豆包支持回车发送，优先尝试回车
            sent = False
            try:
                inp.send_keys(Keys.ENTER)
                sent = True
                logger.info("使用回车键发送消息")
            except:
                pass
            
            # 如果回车不行，再尝试点击发送按钮
            if not sent:
                send_selectors = [
                    "[data-testid='send_button']",
                    "[data-testid='send-button']",
                    "button[type='submit']",
                    "button:has([data-testid='send'])",
                    "[class*='send'] button",
                    ".send-button",
                    "footer button"
                ]
                for sel in send_selectors:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, sel).click()
                        sent = True
                        logger.info(f"使用发送按钮发送: {sel}")
                        break
                    except:
                        continue
            if not sent:
                logger.warning("发送失败，跳过该会话")
                try:
                    self.driver.back()
                    time.sleep(3)
                except:
                    pass
                return None

            # 等待 AI 回复完成
            logger.info("等待豆包回复完成...")
            start_wait = time.time()
            last_length = 0
            while time.time() - start_wait < 90:  # 最长等待90秒
                messages = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid*='message'], .message-item, [class*='message']")
                if messages:
                    last_msg = messages[-1]
                    current_length = len(last_msg.text.strip())
                    if current_length > last_length:
                        last_length = current_length
                        time.sleep(2)
                    else:
                        # 如果长度不变超过3秒，认为回复完成
                        time.sleep(3)
                        if len(last_msg.text.strip()) == last_length:
                            break
                time.sleep(1)
            time.sleep(4)

            messages = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid*='message'], .message-item, [class*='message'], [data-message-id]")
            summary = ""
            logger.info(f"找到 {len(messages)} 条消息")
            
            # 反向遍历，跳过我们发送的prompt，找到豆包最后一次完整回复
            # 豆包的消息通常在最后，且不是我们发送的prompt
            found_summary = False
            prompt_lines = prompt.split('\n')
            prompt_first_line = prompt_lines[0][:30] if prompt_lines else prompt[:30]
            
            for m in reversed(messages):
                txt = m.text.strip()
                if not txt or len(txt) <= 10:
                    continue
                    
                # 跳过我们发送的prompt（通过内容匹配）
                if txt == prompt:
                    continue
                # 如果开头就是prompt的开头，也跳过
                if prompt_first_line in txt[:50]:
                    continue
                # 跳过太短的
                summary = txt
                found_summary = True
                break
            
            # 如果还没找到，放宽条件再找
            if not found_summary:
                logger.debug("放宽条件重新查找总结...")
                for m in reversed(messages):
                    txt = m.text.strip()
                    if txt and len(txt) > 20 and not txt.startswith("帮我完整总结") and not txt.startswith("麻烦你总结"):
                        summary = txt
                        found_summary = True
                        break
            
            # 最后兜底：找所有元素中最长的一段文本（肯定是总结）
            if not found_summary:
                logger.debug("兜底策略：查找最长文本块...")
                try:
                    all_divs = self.driver.find_elements(By.CSS_SELECTOR, "div")
                    max_len = 0
                    for div in all_divs:
                        txt = div.text.strip()
                        if txt and len(txt) > max_len and len(txt) > 50 and not txt.startswith("帮我完整总结"):
                            summary = txt
                            max_len = len(txt)
                except:
                    pass

            logger.info(f"提取到总结长度：{len(summary)}")
            dt_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", summary)
            dt_str = dt_match.group(1) if dt_match else "未知时间"

            title = sess["title"]

            # 解析时间
            try:
                if dt_str != "未知时间":
                    start_time = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                else:
                    start_time = datetime.now()
            except:
                start_time = datetime.now()

            # 创建 SessionData 对象
            session_id = f"doubao_{int(start_time.timestamp())}"
            session_data = SessionData(
                session_id=session_id,
                source=self.name,
                title=title,
                summary=summary,
                start_time=start_time
            )

            # 尝试返回会话列表，如果失败就重新打开主页
            try:
                self.driver.back()
                time.sleep(3)
            except Exception as back_err:
                logger.warning(f"返回列表页失败，重新打开主页：{back_err}")
                error_str = str(back_err).lower()
                # 如果窗口已关闭或session失效，需要重新初始化driver
                if "no such window" in error_str or "invalid session id" in error_str:
                    logger.info("窗口已关闭，重新初始化Chrome...")
                    self._init_driver()
                else:
                    try:
                        self.driver.get("https://www.doubao.com/")
                        time.sleep(5)
                        # 重新点击历史按钮
                        try:
                            history_selectors = [
                                "//*[contains(text(), '历史')]",
                                "//*[contains(text(), '历史对话')]",
                                "[class*='history']",
                                "a[href*='history']"
                            ]
                            found = False
                            for selector in history_selectors:
                                try:
                                    if selector.startswith("//"):
                                        elements = self.driver.find_elements(By.XPATH, selector)
                                    else:
                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    for elem in elements:
                                        if elem.is_displayed():
                                            elem.click()
                                            time.sleep(2)
                                            found = True
                                            break
                                    if found:
                                        break
                                except:
                                    continue
                        except:
                            pass
                        time.sleep(3)
                    except Exception as reopen_err:
                        logger.error(f"重新打开主页失败：{reopen_err}")
                        # 如果重新打开也失败，可能session失效了
                        error_str2 = str(reopen_err).lower()
                        if "no such window" in error_str2 or "invalid session id" in error_str2:
                            logger.info("session失效，重新初始化Chrome...")
                            self._init_driver()

            return session_data

        except Exception as e:
            logger.warning(f"异常：{e}")
            error_str = str(e).lower()
            # 尝试返回列表页，如果失败就重新打开主页
            try:
                self.driver.back()
                time.sleep(3)
            except Exception as back_err:
                logger.warning(f"返回列表页失败，重新打开主页：{back_err}")
                error_str2 = str(back_err).lower()
                # 如果窗口已关闭或session失效，需要重新初始化driver
                if "no such window" in error_str2 or "invalid session id" in error_str2 or "no such window" in error_str:
                    logger.info("窗口已关闭/session失效，重新初始化Chrome...")
                    self._init_driver()
                else:
                    try:
                        self.driver.get("https://www.doubao.com/")
                        time.sleep(5)
                        # 重新点击历史按钮
                        try:
                            history_selectors = [
                                "//*[contains(text(), '历史')]",
                                "//*[contains(text(), '历史对话')]",
                                "[class*='history']",
                                "a[href*='history']"
                            ]
                            found = False
                            for selector in history_selectors:
                                try:
                                    if selector.startswith("//"):
                                        elements = self.driver.find_elements(By.XPATH, selector)
                                    else:
                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    for elem in elements:
                                        if elem.is_displayed():
                                            elem.click()
                                            time.sleep(2)
                                            found = True
                                            break
                                    if found:
                                        break
                                except:
                                    continue
                        except:
                            pass
                        time.sleep(3)
                    except Exception as reopen_err:
                        logger.error(f"重新打开主页失败：{reopen_err}")
                        # 如果重新打开也失败，重新初始化
                        error_str3 = str(reopen_err).lower()
                        if "no such window" in error_str3 or "invalid session id" in error_str3:
                            logger.info("重新打开失败，重新初始化Chrome...")
                            self._init_driver()
            return None

    def _generate_daily_report(self, data: List[SessionData]):
        from collections import defaultdict
        groups = defaultdict(list)

        for sess in data:
            day = sess.start_time.strftime("%Y-%m-%d")
            groups[day].append(sess)

        lines = ["# 豆包对话日报", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]

        for day in sorted(groups.keys(), reverse=True):
            lines.append(f"## {day}")
            lines.append("")
            for sess in groups[day]:
                lines.append(f"### {sess.title}")
                lines.append(f"- 时间：{sess.start_time.strftime('%Y-%m-%d %H:%M')}")
                lines.append("- 总结：")
                lines.append(sess.summary or "")
                lines.append("\n---\n")

        md = "\n".join(lines)
        print("\n" + "=" * 60)
        print(md)
        print("=" * 60)

        from config import get_config
        output_dir = get_config().output_dir
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"doubao_daily_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md)
        logger.info(f"日报已保存到：{output_file}")

    def _hash_title(self, title: str) -> str:
        """对会话标题生成哈希文件名，避免特殊字符问题"""
        import hashlib
        return hashlib.md5(title.encode('utf-8')).hexdigest()[:16]

    def _read_all_messages(self):
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    c = DoubaoSeleniumCollector()
    c.collect(date.today())