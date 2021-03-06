"""
    web服务器返回灵活页面,根据制定的路径打开指定的页面
"""
import socket, threading, multiprocessing,gevent
from gevent import monkey
monkey.patch_all()

# 获取从命令行输入的端口号，跑这个程序需要使用命令行启动:python3 webxxx.py 8888
import sys

class HTTPServer(object):

    def __init__(self, port_num):
        self.port_num = port_num

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # socket优化，避免程序关闭后重启会出现地址重用的问题
        # 参数1：设置socket所在的层级
        # 参数2：设置socket的设置选项，地址重用选项
        # 参数3：设置还是取消，1/0
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定
        server_socket.bind(('', port_num))

        # 监听，设置已完成三次握手队列的长度
        server_socket.listen(128)

        self.server_socket = server_socket


    def request_handler(self, client_socket):
        """ 为每个客户进行服务"""

        # 接收每个客户的请求报文,通过recv_data判断客户端是不是已经断开连接
        recv_data = client_socket.recv(4096)

        if not recv_data:
            print("客户端已经断开连接.")
            client_socket.close()
            return

        # 对请求报文进行切割，获取请求行中的请求路径：a.html
        request_str_data = recv_data.decode()
        data_list = request_str_data.split("\r\n")
        path_info = data_list[0].split(" ")[1]
        print("用户的请求路径为: %s" % path_info)

        if path_info == "/":
            path_info = "/a.html"

        try:
            file = open("./static" + path_info, "rb")
            file_data = file.read()
            file.close()
        except Exception as e:
            # 给客户端回复响应报文,、\r\n == 键盘上的Enter
            response_line = "HTTP/1.1 404 Not Found\r\n"
            # 响应头
            response_header = "Server: PythonWebServer2.0\r\n"
            # 响应体
            response_body = "Error!!!!!!"
            # 拼接豹纹
            response_data = response_line + response_header + "\r\n" + response_body
            """
                发送报文,不能以str的方式方式，需要进行encode
                send() --> 成功发送的字节数,文件大的话，网卡大小可能不会全部发送完毕
                sendAll可以全部发送,不会出现图片显示一半，一半马赛克的情况
            """
            client_socket.sendall(response_data.encode())
        else:
            # 给客户端回复响应报文,、\r\n == 键盘上的Enter
            response_line = "HTTP/1.1 200 OK\r\n"
            # 响应头
            response_header = "Server: PythonWebServer2.0\r\n"
            # 响应体
            response_body = file_data
            # 拼接豹纹
            response_data = (response_line + response_header + "\r\n").encode() + response_body
            # 发送报文,不能以str的方式方式，**不再**需要进行encode
            client_socket.send(response_data)

        # 关闭套接字
        client_socket.close()


    def start(self):

        while True:

            # 队列中取出一个客户端套接字进行服务
            client_socket, client_addr = self.server_socket.accept()

            """
                线程处理每一个客户端的accept，线程你给的变量等是共享的
                所以传入的client_socket和主线程的client_socket是同一个东西，关一个即可
            """
            # thread = threading.Thread(target=request_handler, args=(client_socket,))
            # thread.start()

            """
                线程处理每一个客户端的accept
                在进程copy一份client_socket之后，关闭主进程的client_socket
                由于主进程和子进程互相独立，copy关系，两个都关闭网页左上角才不会一直转
            """
            # proc = multiprocessing.Process(target=self.request_handler, args=(client_socket,))
            # proc.start()
            # client_socket.close()

            """
                gevent协程的方式, join/joinAll就是保证主线程存活的作用，因为此处在while true死循环中，所以不需要join
            """
            gevent.spawn(self.request_handler, client_socket)

def testWeb():

    # sys.argv 存放的是该**进程**运行时候的命令行参数 -> ['basic01.sql', '8888']
    print(sys.argv)
    if len(sys.argv) != 2:
        print("参数个数错误，只需要一个端口号.")
        return

    port_num = sys.argv[1]
    if not port_num.isdigit():
        print("参数个数错误，只需要一个端口号,int类型.")
        return

    http_server = HTTPServer(int(port_num))
    http_server.start()

def main():
    testWeb()


if __name__ == '__main__':
    main()

