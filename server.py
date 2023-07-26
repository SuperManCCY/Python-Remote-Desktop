import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from PIL import ImageGrab
import io
import pyautogui
from jinja2 import Environment, FileSystemLoader

app = FastAPI()

# 获取屏幕分辨率
screen_width, screen_height = pyautogui.size()


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_screenshot(self, screenshot_data: bytes):
        for connection in self.active_connections:
            await connection.send_bytes(screenshot_data)


    async def handle_mouse_move(self, data: str):
        global mouse_x, mouse_y
        # 解析前端发送的鼠标位置信息
        x, y = data.replace("mouseMove:", '').split(",")
        x, y = int(float(x)), int(float(y))
        # 更新鼠标位置信息
        mouse_x, mouse_y = x, y

        # 在服务端电脑上模拟鼠标移动
        pyautogui.moveTo(mouse_x, mouse_y)

    async def handle_mouse_click(self, data: str):
        global mouse_x, mouse_y
        # 解析前端发送的鼠标位置信息
        x, y = data.replace("mouseClick:", '').split(",")
        x, y = int(float(x)), int(float(y))
        # 更新鼠标位置信息
        mouse_x, mouse_y = x, y

        # 在服务端电脑上模拟鼠标移动
        pyautogui.click(mouse_x, mouse_y)

    async def handle_mouse_right_click(self, data: str):
        # 解析前端发送的鼠标右键点击信息
        x, y = data.replace("mouseRightClick:", '').split(",")
        x, y = int(float(x)), int(float(y))

        # 在服务端电脑上模拟鼠标右键点击
        pyautogui.rightClick(x, y)

    async def handle_key_down(self, data: str):
        # 解析前端发送的键盘按下信息
        event, key = data.split(":")

        # 在服务端电脑上模拟键盘按下
        pyautogui.keyDown(key)

    async def handle_key_up(self, data: str):
        # 解析前端发送的键盘松开信息
        event, key = data.split(":")

        # 在服务端电脑上模拟键盘松开
        pyautogui.keyUp(key)


# 创建连接管理器实例
manager = ConnectionManager()


# WebSocket路由
@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:

            data = await websocket.receive_text()
            # print(data)
            if data == "screenshot":

                # 获取屏幕截图
                screenshot = ImageGrab.grab()
                # 对截图进行压缩
                buffered_screenshot = io.BytesIO()
                screenshot.save(buffered_screenshot, format="JPEG", quality=50)
                screenshot_bytes = buffered_screenshot.getvalue()
                # 发送压缩后的截图数据给前端
                await manager.send_screenshot(screenshot_bytes)
                await asyncio.sleep(0.05)

            elif data.startswith("mouseMove"):
                # 处理鼠标位置信息
                # await manager.handle_mouse_move(data)
                pass

            elif data.startswith('mouseRightClick'):
                print(f"鼠标右键点击事件：{data}")
                await manager.handle_mouse_right_click(data)

            elif data.startswith('mouseClick'):
                print(f"鼠标左键点击事件：{data}")
                await manager.handle_mouse_click(data)

            elif data.startswith('keyDown'):
                print(f"键盘按下事件：{data}")
                await manager.handle_key_down(data)

            elif data.startswith('keyUp'):
                print(f"键盘松开事件：{data}")
                await manager.handle_key_up(data)

            # 其他处理鼠标点击、键盘事件等操作...

    except Exception as e:
        print(f"error:{e}")
        manager.disconnect(websocket)


# 使用jinja2渲染HTML模板
env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("index.html")


# 主页，返回一个简单的HTML页面作为客户端
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return template.render(screen_width=screen_width, screen_height=screen_height)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)